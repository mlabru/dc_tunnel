# -*- coding: utf-8 -*-
"""
sdk_utl
sdk utilities

2022/fev  1.0  mlabru   initial version (Linux/Python)
"""
# < imports >--------------------------------------------------------------------------------------

import logging
# import socket

# -------------------------------------------------------------------------------------------------
def sendall(f_sock, f_data):
    """
    send data through socket
    """
    # for all data bytes...
    while len(f_data) > 0:
        try:
            # send data
            li_sent = f_sock.send(f_data)
            # adjust data buffer 
            f_data = f_data[li_sent:]

        # em caso de erro,...    
        except BlockingIOError:
            # logger
            logging.error("blocking io error")

# < the end >--------------------------------------------------------------------------------------
