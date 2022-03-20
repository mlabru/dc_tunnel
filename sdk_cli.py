# -*- coding: utf-8 -*-
"""
sdk_cli
simulate datachannel client point

2022/fev  1.0  mlabru   initial version (Linux/Python)
"""
# < imports >--------------------------------------------------------------------------------------

import logging
import select
import socket
import struct
import sys
import time

# local
import sdk_def as dfs
import sdk_utl as utl

# < defines >--------------------------------------------------------------------------------------
    
# logging level
# DI_LOG_LEVEL = logging.INFO

# < module data >----------------------------------------------------------------------------------

# logger
M_LOG = logging.getLogger(__name__)
M_LOG.setLevel(dfs.DI_LOG_LEVEL)

# -------------------------------------------------------------------------------------------------
def start(ft_datachannel, ft_client):
    """
    reconnect if we go too long with out a ping, the keepalive was a little too platform
    specific so it was easier just to add support right into the protocol instead
    """
    # logger
    M_LOG.info("sdk_cli: %s / %s", str(ft_datachannel), str(ft_client))

    # connected flag
    lv_ds_connected = False

    # create client socket
    l_cls = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    assert l_cls
    # setup client socket
    l_cls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # bind to client port
    l_cls.bind(ft_client)
    # listen 1 queue
    l_cls.listen(1)

    # connected client socket
    l_csock = None

    # last activity time
    lf_last_ping = time.time()

    # init buffer
    ls_buf = b""

    # keep running...
    while True:
        # datachannel is not connected ?  
        if not lv_ds_connected:
            # connect to datachannel
            try:
                # create datachannel socket
                l_dcs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                assert l_dcs
                # setup datachannel socket
                l_dcs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                # connect to datachannel
                l_dcs.connect(ft_datachannel)
                # set the socket into blocking mode
                l_dcs.settimeout(None)

                # last activity
                lf_last_ping = time.time()

                # logger
                M_LOG.info("connected to datachannel at %s.", str(int(lf_last_ping)))

            # em caso de erro,...
            except Exception as err:
                # logger
                M_LOG.error("connection error: %s.", str(err))
                # wait 5s
                time.sleep(5)
                # next try
                continue
                
            # datachannel is connected 
            lv_ds_connected = True

        # handlers to read
        lrd = [l_dcs, l_cls]
        # handlers to write
        lwr = []
        # handlers with error
        ler = [l_dcs]

        # is client connected ?  
        if l_csock is not None:
            # enable to read
            lrd.append(l_csock)
            # enable to error
            ler.append(l_csock)

        # monitors handlers until they become readable or writable, or a communication error occurs
        lrd, lwr, ler = select.select(lrd, lwr, ler, 1)
        '''
        # too long (15s) without a ping ?
        if time.time() - lf_last_ping > 15:
            # force reconnect
            lv_ds_connected = False
            # close datachannel socket
            l_dcs.close()
            # try again
            continue
        '''
        # datachannel connection with error ?
        if l_dcs in ler:
            # is client connected ?
            if l_csock is not None:
                # so just close the client back out
                l_csock.close()
                l_csock = None

            # reset datachannel socket
            l_dcs.close()
            l_dcs = None

            # logger
            M_LOG.warning("datachannel connection with error.")

            # try next
            continue

        # client connection requested ?
        if l_cls in lrd:
            # logger
            M_LOG.info("client connection requested...")
            # accept incoming connection
            l_csock, l_addr = l_cls.accept()
            M_LOG.debug("client connection from: (%s, %s)", str(l_csock), str(l_addr))
            # set the socket into blocking mode
            l_csock.settimeout(None)
            # remove handler from read select
            lrd.remove(l_cls)

            # is datachannel connected ?
            if l_dcs is not None:
                # logger
                M_LOG.info("datachannel notified of connection.")
                # send command (MSG_CONNECT_TARGET) via datachannel
                l_dcs.send(struct.pack(">B", dfs.DI_MSG_CONNECT_TARGET))

            # senão, no datachannel
            else:
                # logger
                M_LOG.warning("no datachannel connection yet")
                # so just close the client back out
                l_csock.close()
                l_csock = None

        # received data from client ?
        if l_csock in lrd:
            # logger
            M_LOG.info("data received from client to target at %s.", str(int(lf_last_ping)))

            # receive data from client
            l_data = l_csock.recv(4096)

            # is datachannel connected and data ok ?
            if (l_dcs is not None) and (len(l_data) > 0):
                # set socket into unblocking mode
                l_dcs.settimeout(0)
                # last activity
                lf_last_ping = time.time()
                # transform it into the format the datachannel expects
                utl.sendall(l_dcs, struct.pack(">BI", dfs.DI_MSG_DATA_TO_TARGET, len(l_data)) + l_data)
                # set the socket into blocking mode
                l_dcs.settimeout(None)

                # logger
                M_LOG.info("%s bytes sent to target.", str(len(l_data)))

            # senão, no datachannel
            else:
                # logger
                M_LOG.warning("no datachannel connection or invalid data length from client.")
                # so just close the client back out
                l_csock.close()
                l_csock = None

            # next
            continue

        # data from datachannel ?
        if l_dcs in lrd:
            # receive data from datachannel 
            l_data = l_dcs.recv(4096)
            # logger
            M_LOG.info("received %s bytes from datachannel at %s.", str(len(l_data)), str(int(lf_last_ping)))

            # no data ?
            if not l_data:
                # try to get connected again
                lv_ds_connected = False

                # is client connected  
                if l_csock is not None:
                    # close client socket
                    l_csock.close()
                    l_csock = None

                # try again
                continue

            # append data in buffer
            ls_buf = ls_buf + l_data

            # process buffer
            while len(ls_buf) > 0:
                # get command
                li_cmd = ls_buf[0]
                M_LOG.debug("command: %s", str(li_cmd))

                # disconnect command ?
                if dfs.DI_MSG_DISCONNECT_TARGET == li_cmd:
                    # logger
                    M_LOG.debug("MSG_DISCONNECT_TARGET command")

                    # last activity
                    lf_last_ping = time.time()
                    # is client connected  
                    if l_csock is not None:
                        # close client socket
                        l_csock.close()
                        l_csock = None

                    # adjust buffer (skip command byte)
                    ls_buf = ls_buf[1:]

                    # go next
                    continue

                # receive data to client command ?
                elif dfs.DI_MSG_DATA_TO_CLIENT == li_cmd:
                    # logger
                    M_LOG.debug("MSG_DATA_TO_CLIENT command")

                    # last activity
                    lf_last_ping = time.time()

                    # data length (int 4 bytes)
                    li_sz = ls_buf[1] << 24 | ls_buf[2] << 16 | ls_buf[3] << 8 | ls_buf[4]

                    # valid buffer size ?
                    if len(ls_buf) >= (1 + 4 + li_sz):
                        # data
                        l_data = ls_buf[1 + 4:1 + 4 + li_sz]
                        # adjust buffer
                        ls_buf = ls_buf[1 + 4 + li_sz:]

                        # is client connected ?
                        if l_csock is not None:
                            # set socket into unblocking mode
                            l_csock.settimeout(0)
                            # send all data
                            utl.sendall(l_csock, l_data)
                            # set socket into blocking mode
                            l_csock.settimeout(None)

                    # senão,...
                    else:
                        # logger
                        M_LOG.error("invalid data length.")
                        # abort
                        break

                # keep alive cmd ?
                elif dfs.DI_MSG_KEEP_ALIVE == li_cmd:
                    # logger
                    M_LOG.debug("DI_MSG_KEEP_ALIVE command")

                    # last activity
                    lf_last_ping = time.time()

                    # adjust buffer (skip command byte)
                    ls_buf = ls_buf[1:]

                # senão,...
                else:
                    # unknown command
                    raise Exception("unknown command")

# -------------------------------------------------------------------------------------------------
def main():
    """
    drive app
    """
    # the first argument is the datachannel address and the second argument is the client address ?
    if len(sys.argv) < 3:
        # show usage
        print("<datachannel-port> <client-port>")
        # quit
        exit()

    try:
        # local host name
        ls_host_name = socket.gethostname()
        # local host address
        ls_app_ip = socket.gethostbyname(ls_host_name)
        M_LOG.info("device hostname: %s / ip: %s", ls_host_name, ls_app_ip)

    # em caso de erro...
    except socket.gaierror:
        # logger
        M_LOG.error("there was an error resolving the host.")
        # quit
        sys.exit()

    # datachannel endpoint
    lt_datachannel = (ls_app_ip, int(sys.argv[1]))

    # client endpoint
    lt_client = (ls_app_ip, int(sys.argv[2]))

    # the address and port pairs are for a TCP/IP connection.
    # ("192.168.15.101", 61001), ("rpi-cam", 5900)
    start(lt_datachannel, lt_client)

# -------------------------------------------------------------------------------------------------
# this is the bootstrap process

if "__main__" == __name__:
    
    # logger
    logging.basicConfig(level=dfs.DI_LOG_LEVEL)

    # disable logging
    # logging.disable(sys.maxint)

    # run application
    main()

# < the end >--------------------------------------------------------------------------------------
