# -*- coding: utf-8 -*-
"""
cli_app
simulate client application

2022/fev  1.0  mlabru   initial version (Linux/Python)
"""
# < imports >--------------------------------------------------------------------------------------

import socket
import sys

# -------------------------------------------------------------------------------------------------
def echo_client(fs_app_ip, fi_app_port):

    # create socket stream
    l_ssck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # connect server port
    l_ssck.connect((fs_app_ip, fi_app_port))

    # init packet number
    li_ndx = 0

    # while ok...
    while True:
        # increment packet number
        li_ndx += 1

        # send packet
        l_ssck.sendall("Hello, world ({})".format(li_ndx).encode())

        # receive response
        l_data = l_ssck.recv(4096)

        # 10000 messages ?
        if 0 == (li_ndx % 10000):
            # log
            print("Received", repr(l_data))

    # close server connection
    l_ssck.close()

# -------------------------------------------------------------------------------------------------
def main():

    # is arguments ok ?
    if len(sys.argv) < 2:
        # log
        print("<app-port>")
        # quit
        exit()

    # the first argument is the app port
    li_app_port = int(sys.argv[1])

    try:
        # local host name
        ls_host_name = socket.gethostname()
        # local host address
        ls_app_ip = socket.gethostbyname(ls_host_name)
        print("cli app hostname:", ls_host_name, "ip:", ls_app_ip)

    # em caso de erro...
    except socket.gaierror:
        # log
        print("there was an error resolving the host")
        # quit
        sys.exit()

    # start client
    echo_client(ls_app_ip, li_app_port)

# -------------------------------------------------------------------------------------------------
    
main()

# < the end >--------------------------------------------------------------------------------------
