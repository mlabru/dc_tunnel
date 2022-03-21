# -*- coding: utf-8 -*-
"""
sdk_off
simula a parte que inicia a comunicação oferecendo um serviço. Por exemplo uma camera. 

2022/fev  1.0  mlabru   initial version (Linux/Python)
"""
# < imports >--------------------------------------------------------------------------------------

# python library
import asyncio
import json
import logging
import requests

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

    M_LOG.debug("peer_connection: %s", str(l_peer_connection))

    # create data channel
    l_channel = l_peer_connection.createDataChannel("chat")
    assert l_channel

    M_LOG.debug("channel: %s", str(l_channel))

    # ---------------------------------------------------------------------------------------------
    async def send_pings(f_channel):
        """
        send ping message
        """
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
    @channel.on("open")
    def on_open():
        """
        on open
        """
        # logger
        M_LOG.info("channel openned")

        channel.send("Hello from Offerer via Datachannel")
        asyncio.ensure_future(send_pings(channel))

    # ---------------------------------------------------------------------------------------------
    @channel.on("message")
    def on_message(fs_message):
        """
        on message
        """
        # logger
        M_LOG.info("Received via RTC Datachannel: %s", fs_message)


    # create an SDP offer
    l_offer = await l_peer_connection.createOffer()
    assert l_offer
    
    M_LOG.debug("offer: %s", str(l_offer))

    # set local description
    await l_peer_connection.setLocalDescription(l_offer)
    
    # build message
    ldct_message = {"id": DS_ID, 
                    "sdp": l_peer_connection.localDescription.sdp, 
                    "type": l_peer_connection.localDescription.type}
    
    # send offer
    l_resp = requests.post(dfs.DS_SIGNALING_SERVER_URL + "/offer", data=ldct_message)
    M_LOG.debug("status_code: %s", str(l_resp.status_code))
    
    # poll for answer...
    while True:
        # wait answer
        l_resp = requests.get(dfs.DS_SIGNALING_SERVER_URL + "/get_answer")
        M_LOG.debug("l_resp: %s", str(l_resp))

        #  service unavailable ?
        if 503 == l_resp.status_code:
            # logger
            M_LOG.warning("Answer not ready, trying again...")
            # wait 1s
            await asyncio.sleep(1)

        # ok ?
        elif 200 == l_resp.status_code:
            # convert json
            l_data = l_resp.json()

            # answer ?
            if "answer" == l_data["type"]:
                # create session descriptor
                l_rd = rtc.RTCSessionDescription(sdp=l_data["sdp"], type=l_data["type"])
                assert l_rd

                # set remote description
                await l_peer_connection.setRemoteDescription(l_rd)
                M_LOG.debug("remoteDescription: %s", str(l_peer_connection.remoteDescription))

                # forever...  
                while True:
                    # logger
                    # M_LOG.debug("Ready for Stuff")

                    # wait   
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
