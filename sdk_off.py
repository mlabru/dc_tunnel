# -*- coding: utf-8 -*-
"""
sdk_off
simula a parte que inicia a comunicação oferecendo um serviço.

2022/fev  1.0  mlabru   initial version (Linux/Python)
"""
# < imports >--------------------------------------------------------------------------------------

# python library
import asyncio
import json
import logging
import requests

import sys    ####

# aiortc
import aiortc as rtc

# .env
from dotenv import load_dotenv

# local
import sdk_def as dfs

# < defines >--------------------------------------------------------------------------------------

# id do equipamento (p.ex. serial no.)
DS_ID = "CAM5513"

# < module data >----------------------------------------------------------------------------------

# logger
M_LOG = logging.getLogger(__name__)
M_LOG.setLevel(dfs.DI_LOG_LEVEL)

aiortc_logger = logging.getLogger("aiortc")
aiortc_logger.setLevel(logging.ERROR)

aioice_logger = logging.getLogger("aioice")
aioice_logger.setLevel(logging.ERROR)

# -------------------------------------------------------------------------------------------------
async def main():
    """
    drive application
    """
    # logger
    M_LOG.info("Starting")

    # create peer connection
    l_peer_connection = rtc.RTCPeerConnection()
    assert l_peer_connection

    # create data channel
    l_channel = l_peer_connection.createDataChannel("chat")
    assert l_channel

    # logger
    M_LOG.debug("Channel is %s", l_channel.label)

    # ---------------------------------------------------------------------------------------------
    async def send_pings(f_channel):
        """
        send ping message
        """
        # logger
        M_LOG.info("send_pings")
      
        # logger
        M_LOG.debug("Channel is %s", f_channel.label)
      
        # init message counter
        li_num = 0

        # forever...
        while True:
            # build message
            ls_msg = "From Offerer: {}".format(li_num)
            M_LOG.debug("Sending via RTC Datachannel: %s", ls_msg)

            # send message
            f_channel.send(ls_msg)

            # increment number of messages (pings)
            li_num += 1

            # wait 1s
            await asyncio.sleep(1)

    # ---------------------------------------------------------------------------------------------
    @l_channel.on("open")
    def on_open():
        """
        on open
        """
        # logger
        M_LOG.info("on_open: channel openned")
      
        # build message
        ls_msg = "Hello from Offerer via Datachannel (1st offer)"
        
        # send message
        l_channel.send(ls_msg)

        # execute send_pings in the background, without waiting for it to finish
        asyncio.ensure_future(send_pings(l_channel))

    # ---------------------------------------------------------------------------------------------
    @l_channel.on("message")
    def on_message(fs_message):
        """
        on message
        """
        # logger
        M_LOG.info("on_message")
      
        # logger
        M_LOG.debug("Received via RTC Datachannel: %s", fs_message)

    # ---------------------------------------------------------------------------------------------

    # create an SDP offer
    l_offer = await l_peer_connection.createOffer()
    assert l_offer
    
    # set local description
    await l_peer_connection.setLocalDescription(l_offer)
    
    # build message
    ldct_message = {"id": DS_ID, 
                    "sdp": l_peer_connection.localDescription.sdp, 
                    "type": l_peer_connection.localDescription.type}
    
    # send offer
    l_resp = requests.post(dfs.DS_SIGNALING_SERVER_URL + "/offer", data=ldct_message)
    
    # poll for answer...
    while True:
        # wait answer
        l_resp = requests.get(dfs.DS_SIGNALING_SERVER_URL + "/get_answer")

        #  service unavailable ?
        if 503 == l_resp.status_code:
            # logger
            M_LOG.warning("Answer not ready, trying again...")
            # wait 1s
            await asyncio.sleep(1)

        # ok ?
        elif 200 == l_resp.status_code:
            # convert received response to json
            l_data = l_resp.json()

            # answer ?
            if "answer" == l_data["type"]:
                # create session descriptor with sdp/type from answer
                l_sd = rtc.RTCSessionDescription(sdp=l_data["sdp"], type=l_data["type"])
                assert l_sd

                # set remote description
                await l_peer_connection.setRemoteDescription(l_sd)

                # forever...  
                while True:
                    # keep background work running
                    await asyncio.sleep(1)

            # otherwise,... 
            else:
                # logger
                M_LOG.error("Wrong type.")

            # quit
            break

        # logger
        M_LOG.debug("status code: %s", str(l_resp.status_code))

# -------------------------------------------------------------------------------------------------
# this is the bootstrap process

if "__main__" == __name__:

    # logger
    logging.basicConfig(level=dfs.DI_LOG_LEVEL)

    # disable logging
    # logging.disable(sys.maxint)

    # run application
    asyncio.run(main())

# < the end >--------------------------------------------------------------------------------------
