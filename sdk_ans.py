# -*- coding: utf-8 -*-
"""
sdk_ans
simula a parte que responde a comunicação de oferta de um serviço.

2022/fev  1.0  mlabru   initial version (Linux/Python)
"""
# < imports >--------------------------------------------------------------------------------------

# python library
import asyncio
import logging
import requests

import sys ###

# aiortc
from aiortc import RTCIceCandidate, RTCPeerConnection, RTCSessionDescription, RTCConfiguration, RTCIceServer

# .env
from dotenv import load_dotenv

# local
import sdk_def as dfs

# < defines >--------------------------------------------------------------------------------------

# id do equipamento (p.ex. serial no.)
DS_ID = "answerer01"

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
    M_LOG.info("Starting")

    # create peer connection
    l_peer_connection = RTCPeerConnection()
    assert l_peer_connection

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
            ls_msg = "From Answerer: {}".format(li_num)
            M_LOG.debug("Sending via RTC Datachannel: %s", ls_msg)

            # send message
            f_channel.send(ls_msg)

            # increment message counter
            li_num += 1

            # wait 1s
            await asyncio.sleep(1)

    # ---------------------------------------------------------------------------------------------
    @l_peer_connection.on("datachannel")
    def on_datachannel(f_channel):
        """
        on datachannel
        """
        # logger
        M_LOG.info("on_datachannel")

        # logger
        M_LOG.debug("%s - created by remote party", str(f_channel.label))

        # send message
        f_channel.send("Hello from Answerer via RTC Datachannel (1st answer)")

        @f_channel.on("message")
        async def on_message(f_message):
            # logger
            M_LOG.info("on_message")

            # logger
            M_LOG.debug("Received via RTC Datachannel: %s", str(f_message))

        # send pings
        asyncio.ensure_future(send_pings(f_channel))
    
    # ---------------------------------------------------------------------------------------------

    # search for an offer
    l_resp = requests.get(dfs.DS_SIGNALING_SERVER_URL + "/get_offer")

    # ok ?
    if 200 == l_resp.status_code:
        # convert json
        l_data = l_resp.json()

        # offer ?
        if "offer" == l_data["type"]:
            # create session descriptor with sdp/type from offer
            l_rd = RTCSessionDescription(sdp=l_data["sdp"], type=l_data["type"])
            assert l_rd

            # set remote description
            await l_peer_connection.setRemoteDescription(l_rd)
            # set local description
            await l_peer_connection.setLocalDescription(await l_peer_connection.createAnswer())
 
            # build message
            ldct_message = {"id": DS_ID, 
                            "sdp": l_peer_connection.localDescription.sdp, 
                            "type": l_peer_connection.localDescription.type}

            # send answer
            l_resp = requests.post(dfs.DS_SIGNALING_SERVER_URL + '/answer', data=ldct_message)

            # forever...
            while True:
                # keep background work running
                await asyncio.sleep(1)

        # otherwise,... 
        else:
            # logger
            M_LOG.error("Wrong type.")

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
