# -*- coding: utf-8 -*-
"""
tgt_app
simulate target application

2022/fev  1.0  mlabru   initial version (Linux/Python)
"""
# < imports >--------------------------------------------------------------------------------------

import socket
import sys

# import glb_defs as defs

# -------------------------------------------------------------------------------------------------
def echo_server(fs_app_ip, fi_app_port):

    # create socket stream
    l_ssck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # bind local port
    l_ssck.bind((fs_app_ip, fi_app_port))

    # listening for incoming connections
    l_ssck.listen(1)

    # accept an incoming connection
    l_conn, l_addr = l_ssck.accept()
    print("client:", l_conn, l_addr)

    # while ok...
    while 1:
        # read client data
        l_data = l_conn.recv(4096)
       
        if not l_data:
            # quit while 
            break

        # send all incoming data back (echo)
        l_conn.sendall(l_data)

    # close client connection
    l_conn.close()
    
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
        print("app hostname:", ls_host_name, "ip:", ls_app_ip)
        
    # em caso de erro...
    except socket.gaierror:
        # log
        print("there was an error resolving the host")
        # quit
        sys.exit()

    # start server
    echo_server(ls_app_ip, li_app_port)

# -------------------------------------------------------------------------------------------------
        
main()
            
# < the end >--------------------------------------------------------------------------------------
