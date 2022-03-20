# -*- coding: utf-8 -*-
"""
sdk_tgt
simulate datachannel target side

2022/fev  1.0  mlabru   initial version (Linux/Python)
"""
# < imports >--------------------------------------------------------------------------------------

import logging
import socket
import select
import struct
import sys
import time

# local
import sdk_def as dfs
import sdk_utl as utl

# < defines >--------------------------------------------------------------------------------------

# logging level
DI_LOG_LEVEL = logging.DEBUG
    
# < module data >----------------------------------------------------------------------------------

# logger
M_LOG = logging.getLogger(__name__)
M_LOG.setLevel(DI_LOG_LEVEL)

# -------------------------------------------------------------------------------------------------
def create_datachannel(ft_datachannel):
    """
    create datachannel
    """
    # create datachannel socket
    l_dcs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    assert l_dcs
    
    # setup datachannel socket
    l_dcs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # bind to datachannel port
    l_dcs.bind(ft_datachannel)
    # listen 1 queue
    l_dcs.listen(1)

    # return
    return l_dcs
    
# -------------------------------------------------------------------------------------------------
def start(ft_datachannel, ft_target):

    # logger
    M_LOG.info("sdk_tgt: %s / %s", str(ft_datachannel), str(ft_target))

    # create datachannel socket
    l_dcs = create_datachannel(ft_datachannel)

    # connected datachannel socket
    l_dsock = None

    # connected target socket
    l_tsock = None

    # data buffer
    ls_buf = b""

    # last activity time
    li_last_ping = time.time()

    # loop...
    while True:
        # handlers to read
        lrd = [l_dcs]
        # handlers to write
        lwr = []
        # handlers with error
        ler = [l_dcs]

        # is datachannel connected ? 
        if l_dsock is not None:
            # enable to read
            lrd.append(l_dsock)
            # enable to error
            ler.append(l_dsock)

        # is target connected ?            
        if l_tsock is not None:
            # enable to read
            lrd.append(l_tsock)
            # enable to error
            ler.append(l_tsock)

        # monitors handlers until they become readable or writable, or a communication error occurs
        lrd, lwr, ler = select.select(lrd, lwr, ler, 1)
        '''
        # last activity longer than 15 sec ?
        if time.time() - li_last_ping > 15:
            # last activity time
            li_last_ping = time.time()

            # is datachannel connected ?
            if l_dsock is not None:
                # send a little ping to help the target determine when the 
                # connection has dropped and it needs to be re-established
                utl.sendall(l_dsock, struct.pack(">B", dfs.DI_MSG_KEEP_ALIVE))
        '''
        # datachannel connection with error ?
        if l_dsock in ler:
            # logger
            M_LOG.warning("datachannel connection with error.")
            # remove handler from error select
            ler.remove(l_dsock)
            # reset datachannel socket
            l_dsock.close()
            l_dsock = None

            # is target connected ?
            if l_tsock is not None:
                # so just close the target back out
                l_tsock.close()
                l_tsock = None

        # target connection with error ?        
        if l_tsock in ler:
            # logger
            M_LOG.warning("target connection with error.")
            # send disconnect command (MSG_DISCONNECT_TARGET) via datachannel
            l_dsock.send(struct.pack(">B", dfs.DI_MSG_DISCONNECT_TARGET))
            # remove handler from error select
            ler.remove(l_tsock)

            # is target connected ?
            if l_tsock is not None:
                # so just close the target back out
                l_tsock.close()
                l_tsock = None

        # datachannel connection requested ?
        if l_dcs in lrd:
            # logget
            M_LOG.info("datachannel connection request...")
            # accept incoming connection
            l_dsock, l_addr = l_dcs.accept()
            M_LOG.debug("connection requested from: %s %s", str(l_dsock), str(l_addr))
            # set the socket into blocking mode
            l_dsock.settimeout(None)
            # remove handler from read select
            lrd.remove(l_dcs)
        '''
        # target connection requested ?
        if l_cls in lrd:
            # log
            print("target connection request")
            # accept incoming connection
            l_tsock, addr = l_cls.accept()
            print("from:", l_tsock, addr)
            # set the socket into blocking mode
            l_tsock.settimeout(None)
            # remove handler from read select
            lrd.remove(l_cls)
            
            # is datachannel connected ? 
            if l_dsock is not None:
                # log
                print("   datachannel notified of connection")
                # send command (MSG_CONNECT_TARGET) via datachannel
                l_dsock.send(struct.pack(">B", dfs.DI_MSG_CONNECT_TARGET))

            # senão, no datachannel
            else:
                # so just close the target back out
                l_tsock.close()
                l_tsock = None
        '''        
        # only tsock or dsock should be here now
        for l_sock in lrd:
            # receive data from this source
            try:
                l_data = l_sock.recv(4096)
                # logger
                M_LOG.info("received %s bytes.", str(len(l_data)))

            # em caso de erro,... 
            except ConnectionResetError:
                # logger
                M_LOG.error("connection reset error")
                # reset data
                l_data = None

            # no data ?
            if not l_data:
                # datachannel eof ?
                if l_dsock is l_sock:
                    # so just close the datachannel
                    l_dsock.close()
                    l_dsock = None
                    # logger
                    M_LOG.info("datachannel dropped...")

                    # is target connected ?
                    if l_tsock is not None:
                        # logger
                        M_LOG.info("...dropping target.")
                        # close the target
                        l_tsock.close()
                        l_tsock = None

                    # try again
                    continue
                    
                # target eof ?
                if l_tsock is l_sock:
                    # so just close the target
                    l_tsock.close()
                    l_tsock = None
                    # logger
                    M_LOG.info("target dropped.")

                    # set socket into unblocking mode
                    l_dsock.settimeout(0)
                    # send disconnect command (MSG_DISCONNECT_TARGET) via datachannel
                    utl.sendall(l_dsock, struct.pack(">B", dfs.DI_MSG_DISCONNECT_TARGET))
                    # set the socket into blocking mode
                    l_dsock.settimeout(None)

                    # try again
                    continue

            # received data from datachannel ?
            if l_dsock is l_sock:
                # logger
                M_LOG.info("data received from client to target.")

                # append data in buffer
                ls_buf = ls_buf + l_data
                
                # process buffer
                while len(ls_buf) > 0:
                    # get command
                    li_cmd = ls_buf[0]
                    M_LOG.debug("command: %s", str(li_cmd))
                    
                    # disconnect target command ?
                    if dfs.DI_MSG_DISCONNECT_TARGET == li_cmd:
                        # logger
                        M_LOG.debug("MSG_DISCONNECT_TARGET command")
                        # last activity
                        li_last_ping = time.time()

                        # is target connected
                        if l_tsock is not None:
                            # close target socket
                            l_tsock.close()
                            l_tsock = None

                        # adjust buffer (skip command byte)
                        ls_buf = ls_buf[1:]

                        # go next
                        continue

                    # connect target command ?
                    elif dfs.DI_MSG_CONNECT_TARGET == li_cmd:
                        # logger
                        M_LOG.debug("MSG_CONNECT_TARGET command")
                        # last activity
                        li_last_ping = time.time()

                        # is target already connected ?
                        if l_tsock is not None:
                            # close target socket
                            l_tsock.close()
                            l_tsock = None

                        # create target socket
                        l_tsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        assert l_tsock

                        # connect to target
                        l_tsock.connect(ft_target)
                        # set the socket into blocking mode
                        l_tsock.settimeout(None)

                        # adjust buffer (skip command byte)
                        ls_buf = ls_buf[1:]

                    # data to target command ?
                    elif dfs.DI_MSG_DATA_TO_TARGET == li_cmd:
                        # logger
                        M_LOG.debug("MSG_DATA_TO_TARGET command")
                        # last activity
                        li_last_ping = time.time()

                        # data length (int with 4 bytes)
                        li_sz = ls_buf[1] << 24 | ls_buf[2] << 16 | ls_buf[3] << 8 | ls_buf[4]

                        # valid buffer size ?
                        if len(ls_buf) >= (1 + 4 + li_sz):
                            # data
                            l_data = ls_buf[1 + 4: 1 + 4 + li_sz]
                            # adjust buffer
                            ls_buf = ls_buf[1 + 4 + li_sz:]

                            # is target connected ?
                            if l_tsock is not None:
                                # set socket into unblocking mode
                                l_tsock.settimeout(0)
                                # send all data
                                utl.sendall(l_tsock, l_data)
                                # set socket into blocking mode
                                l_tsock.settimeout(None)

                        # senão, lost data buffer pointer
                        else:
                            # logger
                            M_LOG.error("invalid data length.")
                            # quit
                            break

                    # keep alive command ?
                    elif dfs.DI_MSG_KEEP_ALIVE == li_cmd:
                        # logger
                        M_LOG.debug("MSG_KEEP_ALIVE command")
                        # last activity
                        li_last_ping = time.time()
                        
                        # adjust buffer (skip command byte)
                        ls_buf = ls_buf[1:]

                    # senão,...
                    else:
                        # unknown command
                        raise Exception("unknown command")

                # next    
                continue

            # received from target ?
            if l_tsock is l_sock:
                # logger
                M_LOG.info("data received from target to client.")
                 
                # is datachannel connected and data ok ?    
                if (l_dsock is not None) and (len(l_data) > 0):
                    # set socket into unblocking mode
                    l_dsock.settimeout(0)
                    # last activity
                    li_last_ping = time.time()
                    # transform it into the format the datachannel expects
                    utl.sendall(l_dsock, struct.pack(">BI", dfs.DI_MSG_DATA_TO_CLIENT, len(l_data)) + l_data)
                    # set the socket into blocking mode
                    l_dsock.settimeout(None)
                    # logger
                    M_LOG.debug("target sent %s bytes to client.", str(len(l_data)))

                # next    
                continue

# -------------------------------------------------------------------------------------------------
def main():

    # args
    llst_args = sys.argv

    # error in args ?
    if len(llst_args) < 2:
        # log
        print("<datachannel-port> <target-port>")
        # quit
        exit()

    # datachannel port
    li_datachannel = int(llst_args[1])
    # target port
    li_target = int(llst_args[2])

    # keep running...
    while True:
        try:
            # make connections
            start(("192.168.15.101", li_datachannel), ("192.168.15.101", li_target))

        # em caso de erro,...
        except Exception as err:
            # logger
            M_LOG.error(err)
            M_LOG.info("failure restarting")

# -------------------------------------------------------------------------------------------------
# this is the bootstrap process

if "__main__" == __name__:

    # logger
    logging.basicConfig(level=DI_LOG_LEVEL)

    # disable logging
    # logging.disable(sys.maxint)
    
    # run application
    main()

# < the end >--------------------------------------------------------------------------------------
