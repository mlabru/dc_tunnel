# -*- coding: utf-8 -*-
"""
cli_sdk
simulate datachannel client side

2022/fev  1.0  mlabru   initial version (Linux/Python)
"""
# < imports >--------------------------------------------------------------------------------------

import socket
import select
import struct
import sys
import time

# -------------------------------------------------------------------------------------------------
def start(ft_datachannel, ft_client):

    # create datachannel socket
    dcs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # setup datachannel socket
    dcs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # bind to datachannel port
    dcs.bind(ft_datachannel)
    # listen 1 queue
    dcs.listen(1)

    # connected datachannel socket
    dsock = None

    # create client socket
    cls = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # setup client socket
    cls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # bind to client port
    cls.bind(ft_client)
    # listen 1 queue
    cls.listen(1)

    # connected client socket
    csock = None

    # last activity time
    lastping = time.time()

    # list of datachannels
    # llst_datachannels = []

    # loop...
    while True:
        # handlers to read
        lrd = [dcs, cls]
        # handlers to write
        lwr = []
        # handlers with error
        ler = []

        # is datachannel connected ? 
        if dsock is not None:
            # enable to read
            lrd.append(dsock)
            # enable to error
            ler.append(dsock)

        # is client connected ?            
        if csock is not None:
            # enable to read
            lrd.append(csock)
            # enable to error
            ler.append(csock)

        # monitors handlers until they become readable or writable, or a communication error occurs
        lrd, lwr, ler = select.select(lrd, lwr, ler, 1)

        # last activity longer than 5 sec ?
        if time.time() - lastping > 5:
            # last activity time
            lastping = time.time()
            # is datachannel connected ?
            if dsock is not None:
                # send a little ping to help the client determine when the 
                # connection has dropped and it needs to be re-established
                sendall(dsock, struct.pack(">B", 3))

        # datachannel connection requested ?
        if dcs in lrd:
            # log
            print("datachannel connection request")
            # accept incoming connection
            dsock, addr = dcs.accept()
            print("from:", dsock, addr)
            # set the socket into blocking mode
            dsock.settimeout(None)
            # remove handler from read select
            lrd.remove(dcs)

        # client connection requested ?
        if cls in lrd:
            # log
            print("client connection request")
            # accept incoming connection
            csock, addr = cls.accept()
            print("from:", csock, addr)
            # set the socket into blocking mode
            csock.settimeout(None)
            # remove handler from read select
            lrd.remove(cls)
            
            # is datachannel connected ? 
            if dsock is not None:
                # log
                print("   datachannel notified of connection")
                # send command (1) via datachannel
                dsock.send(struct.pack(">B", 1))

            # senão, no datachannel
            else:
                # so just close the client back out
                csock.close()
                csock = None

        # client connection with error ?        
        if csock in ler:
            # send disconnect command (0) via datachannel
            dsock.send(struct.pack(">B", 0))
            # reset client socket
            csock = None

        # datachannel connection with error ?
        if dsock in ler:
            # is client connected ?
            if csock is not None:
                # so just close the client back out
                csock.close()
                csock = None

            # reset datachannel socket
            dsock = None

        # only csock or dsock should be here now
        for sock in lrd:
            # recieve data from this client
            try:
                data = sock.recv(4096)

            # em caso de erro,... 
            except ConnectionResetError:
                # log
                print("connection reset error")
                # reset data
                data = False

            # no data ?
            if not data:
                # datachannel eof ?
                if dsock is sock:
                    # log
                    print("datachannel dropped")
                    # is client connected ?
                    if csock is not None:
                        # log
                        print("    dropping client")
                        # close the client
                        csock.close()
                        csock = None

                    # so just close the datachannel
                    dsock = None
                    # try again
                    continue
                    
                # client eof ?
                if csock is sock:
                    # log
                    print("client dropped")

                    # set socket into unblocking mode
                    csock.settimeout(0)
                    # send disconnect command (0) via datachannel
                    sendall(dsock, struct.pack(">B", 0))
                    # set the socket into blocking mode
                    csock.settimeout(None)
                    # close the client
                    csock = None

                    # try again
                    continue

            # received from datachannel ?
            if dsock is sock:
                # log
                print("data received (datachannel -> client)")
    
                # is client connected ?
                if csock is not None:
                    # set socket into unblocking mode
                    csock.settimeout(0)
                    # send packet as raw data to the client
                    sendall(csock, data)
                    # set the socket into blocking mode
                    csock.settimeout(None)

                # next    
                continue

            # received from client ?
            if csock is sock:
                # log
                print("data received (client -> datachannel) %s" % len(data))
                 
                # is datachannel connected and data ok ?    
                if dsock is not None and len(data) > 0:
                    # set socket into unblocking mode
                    dsock.settimeout(0)
                    # last activity
                    lastping = time.time()
                    # transform it into the format the datachannel expects
                    sendall(dsock, struct.pack(">BI", 2, len(data)) + data)
                    # set the socket into blocking mode
                    dsock.settimeout(None)

                # next    
                continue

# -------------------------------------------------------------------------------------------------
def sendall(f_sock, f_data):

    # for all data bytes...
    while len(f_data) > 0:
        try:
            # send data
            li_sent = f_sock.send(f_data)
            # adjust data buffer 
            f_data = f_data[li_sent:]

        # em caso de erro,...    
        except BlockingIOError:
            # log
            print("blocking io error")

# -------------------------------------------------------------------------------------------------
def main():

    # args
    llst_args = sys.argv

    # error in args ?
    if len(llst_args) < 2:
        # log
        print("<datachannel-port> <client-port>")
        # quit
        exit()

    # datachannel port
    li_datachannel = int(llst_args[1])
    # client port
    li_client = int(llst_args[2])

    # keep running...
    while True:
        try:
            # make connections
            start(("0.0.0.0", li_datachannel), ("0.0.0.0", li_client))

        # em caso de erro,...
        except Exception as e:
            # log
            print(e)
            print("failure restarting")

# -------------------------------------------------------------------------------------------------

main()

# < the end >--------------------------------------------------------------------------------------
