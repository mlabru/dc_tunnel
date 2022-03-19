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
    l_dcs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # setup datachannel socket
    l_dcs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # bind to datachannel port
    l_dcs.bind(ft_datachannel)
    # listen 1 queue
    l_dcs.listen(1)

    # connected datachannel socket
    l_dsock = None

    # create client socket
    l_cls = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # setup client socket
    l_cls.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    # bind to client port
    l_cls.bind(ft_client)
    # listen 1 queue
    l_cls.listen(1)

    # connected client socket
    l_csock = None

    # last activity time
    li_last_ping = time.time()

    # loop...
    while True:
        # handlers to read
        lrd = [l_dcs, l_cls]
        # handlers to write
        lwr = []
        # handlers with error
        ler = []

        # is datachannel connected ? 
        if l_dsock is not None:
            # enable to read
            lrd.append(l_dsock)
            # enable to error
            ler.append(l_dsock)

        # is client connected ?            
        if l_csock is not None:
            # enable to read
            lrd.append(l_csock)
            # enable to error
            ler.append(l_csock)

        # monitors handlers until they become readable or writable, or a communication error occurs
        lrd, lwr, ler = select.select(lrd, lwr, ler, 1)

        # last activity longer than 5 sec ?
        if time.time() - li_last_ping > 5:
            # last activity time
            li_last_ping = time.time()
            # is datachannel connected ?
            if l_dsock is not None:
                # send a little ping to help the client determine when the 
                # connection has dropped and it needs to be re-established
                sendall(l_dsock, struct.pack(">B", 3))

        # datachannel connection requested ?
        if l_dcs in lrd:
            # log
            print("datachannel connection request")
            # accept incoming connection
            l_dsock, addr = l_dcs.accept()
            print("from:", l_dsock, addr)
            # set the socket into blocking mode
            l_dsock.settimeout(None)
            # remove handler from read select
            lrd.remove(l_dcs)

        # client connection requested ?
        if l_cls in lrd:
            # log
            print("client connection request")
            # accept incoming connection
            l_csock, addr = l_cls.accept()
            print("from:", l_csock, addr)
            # set the socket into blocking mode
            l_csock.settimeout(None)
            # remove handler from read select
            lrd.remove(l_cls)
            
            # is datachannel connected ? 
            if l_dsock is not None:
                # log
                print("   datachannel notified of connection")
                # send command (1) via datachannel
                l_dsock.send(struct.pack(">B", 1))

            # senão, no datachannel
            else:
                # so just close the client back out
                l_csock.close()
                l_csock = None

        # client connection with error ?        
        if l_csock in ler:
            # send disconnect command (0) via datachannel
            l_dsock.send(struct.pack(">B", 0))
            # reset client socket
            l_csock = None

        # datachannel connection with error ?
        if l_dsock in ler:
            # is client connected ?
            if l_csock is not None:
                # so just close the client back out
                l_csock.close()
                l_csock = None

            # reset datachannel socket
            l_dsock = None

        # only csock or dsock should be here now
        for l_sock in lrd:
            # recieve data from this client
            try:
                l_data = l_sock.recv(4096)

            # em caso de erro,... 
            except ConnectionResetError:
                # log
                print("connection reset error")
                # reset data
                l_data = None

            # no data ?
            if not l_data:
                # datachannel eof ?
                if l_dsock is l_sock:
                    # log
                    print("datachannel dropped")
                    # is client connected ?
                    if l_csock is not None:
                        # log
                        print("    dropping client")
                        # close the client
                        l_csock.close()
                        l_csock = None

                    # so just close the datachannel
                    l_dsock = None
                    # try again
                    continue
                    
                # client eof ?
                if l_csock is l_sock:
                    # log
                    print("client dropped")

                    # set socket into unblocking mode
                    l_csock.settimeout(0)
                    # send disconnect command (0) via datachannel
                    sendall(l_dsock, struct.pack(">B", 0))
                    # set the socket into blocking mode
                    l_csock.settimeout(None)
                    # close the client
                    l_csock = None

                    # try again
                    continue

            # received from datachannel ?
            if l_dsock is l_sock:
                # log
                print("data received (datachannel -> client)")
    
                # is client connected ?
                if l_csock is not None:
                    # set socket into unblocking mode
                    l_csock.settimeout(0)
                    # send packet as raw data to the client
                    sendall(l_csock, l_data)
                    # set the socket into blocking mode
                    l_csock.settimeout(None)

                # next    
                continue

            # received from client ?
            if l_csock is l_sock:
                # log
                print("data received (client -> datachannel) %s" % len(l_data))
                 
                # is datachannel connected and data ok ?    
                if (l_dsock is not None) and (len(l_data) > 0):
                    # set socket into unblocking mode
                    l_dsock.settimeout(0)
                    # last activity
                    li_last_ping = time.time()
                    # transform it into the format the datachannel expects
                    sendall(l_dsock, struct.pack(">BI", 2, len(l_data)) + l_data)
                    # set the socket into blocking mode
                    l_dsock.settimeout(None)

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
