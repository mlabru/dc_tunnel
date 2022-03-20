# -*- coding: utf-8 -*-
"""
tgt_app
simulate target application

2022/fev  1.0  mlabru   initial version (Linux/Python)
"""
# < imports >--------------------------------------------------------------------------------------

import logging
import socket
import sys

# < defines >--------------------------------------------------------------------------------------
    
# logging level
DI_LOG_LEVEL = logging.DEBUG

# < module data >----------------------------------------------------------------------------------

# logger
M_LOG = logging.getLogger(__name__)
M_LOG.setLevel(DI_LOG_LEVEL)

# -------------------------------------------------------------------------------------------------
def echo_server(fs_app_ip, fi_app_port):
    """
    echo server
    """
    # logger
    M_LOG.info("echo_server: %s / %s", str(fs_app_ip), str(fi_app_port))
    
    # create socket stream
    l_ssck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    assert l_ssck

    # setup client socket
    l_ssck.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    # bind local port
    l_ssck.bind((fs_app_ip, fi_app_port))

    # listening for incoming connections
    l_ssck.listen(1)

    # accept an incoming connection
    l_conn, l_addr = l_ssck.accept()
    M_LOG.info("client conn: %s", str(l_conn))
    M_LOG.info("client addr: %s", str(l_addr))

    # init packet number
    li_ndx = 0

    # while ok...
    while 1:
        # increment packet number
        li_ndx += 1

        # read client data
        l_data = l_conn.recv(4096)
       
        if not l_data:
            # quit while 
            break

        # send all incoming data back (echo)
        l_conn.sendall(l_data)

        # 50000 messages ?
        if 0 == (li_ndx % 50000):
            # logger
            M_LOG.debug("Received: %s", str(l_data))

    # close client connection
    l_conn.close()
    
# -------------------------------------------------------------------------------------------------
def main():

    # is arguments ok ?
    if len(sys.argv) < 2:
        # show usage
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
        M_LOG.info("device hostname: %s / ip: %s", ls_host_name, ls_app_ip)
        
    # em caso de erro...
    except socket.gaierror:
        # logger
        M_LOG.error("there was an error resolving the host.")
        # quit
        sys.exit()

    # start server
    echo_server(ls_app_ip, li_app_port)

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
