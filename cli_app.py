# -*- coding: utf-8 -*-
"""
cli_app
simulate client application

2022/fev  1.0  mlabru   initial version (Linux/Python)
"""
# < imports >--------------------------------------------------------------------------------------

import logging
import socket
import sys
import time

# local
import sdk_def as dfs

# < defines >--------------------------------------------------------------------------------------
    
# logging level
# DI_LOG_LEVEL = logging.DEBUG
    
# message counter
DI_MSG_COUNTER = 5

# < module data >----------------------------------------------------------------------------------

# logger
M_LOG = logging.getLogger(__name__)
M_LOG.setLevel(dfs.DI_LOG_LEVEL)

# -------------------------------------------------------------------------------------------------
def echo_client(fs_app_ip, fi_app_port):

    # logger
    M_LOG.info("echo_client: (%s, %s)", fs_app_ip, fi_app_port)
    
    # create socket stream
    l_ssck = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    assert l_ssck

    # connect server port
    l_ssck.connect((fs_app_ip, fi_app_port))

    # init packet number
    li_num = 0

    # while ok...
    while True:
        # increment packet number
        li_num += 1

        # send packet
        l_ssck.sendall("Hello, world ({})".format(li_num).encode())

        # receive response
        l_data = l_ssck.recv(4096)

        # MSG_COUNTER messages ?
        if 0 == (li_num % DI_MSG_COUNTER):
            # logger
            M_LOG.debug("Received: %s", str(l_data))
        
        time.sleep(2) 

    # close server connection
    l_ssck.close()

# -------------------------------------------------------------------------------------------------
def main():

    # is arguments ok ?
    if len(sys.argv) < 2:
        # show usgae
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
        M_LOG.info("cli app hostname: %s / ip: %s", ls_host_name, ls_app_ip)

    # em caso de erro...
    except socket.gaierror:
        # logger
        M_LOG.error("there was an error resolving the host.")
        # quit
        sys.exit()

    # start client
    echo_client(ls_app_ip, li_app_port)

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
