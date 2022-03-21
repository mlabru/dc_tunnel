# -*- coding: utf-8 -*-
"""
sdk_def
system defines

2022/fev  1.0  mlabru   initial version (Linux/Python)
"""
# < imports >--------------------------------------------------------------------------------------

import logging

# < defines >--------------------------------------------------------------------------------------
    
# logging level
DI_LOG_LEVEL = logging.DEBUG

# datachannel messages
DI_MSG_DISCONNECT_TARGET = 0
DI_MSG_CONNECT_TARGET = 1
DI_MSG_DATA_TO_CLIENT = 2
DI_MSG_DATA_TO_TARGET = 3
DI_MSG_KEEP_ALIVE = 4

# signaling server URL
DS_SIGNALING_SERVER_URL = 'http://0.0.0.0:6969'

# id do equipamento (p.ex. serial no.)
# DS_ID = "CAM5513"

# < the end >--------------------------------------------------------------------------------------
