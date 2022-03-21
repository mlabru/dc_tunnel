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

# -------------------------------------------------------------------------------------------------
async def main():
    """
    drive application
    """
    M_LOG.info("Starting")

    # create peer connection
    l_peer_connection = RTCPeerConnection()
    assert l_peer_connection

    M_LOG.debug("peer_connection: %s", str(l_peer_connection))
        
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
            ls_msg = "From Answerer: {}".format(li_num)
            M_LOG.debug("Sending via RTC Datachannel: %s", ls_msg)

            # send message
            f_channel.send(ls_msg)

            # increment message counter
            li_num += 1

            # wait 1s
            await asyncio.sleep(1)

    # ---------------------------------------------------------------------------------------------
    @peer_connection.on("datachannel")
    def on_datachannel(f_channel):
        """
        on open
        """
        # logger
        M_LOG.info("%s - created by remote party", str(f_channel))

        # send message
        f_channel.send("Hello From Answerer via RTC Datachannel")

        @channel.on("message")
        async def on_message(message):
            # logger
            M_LOG.info("Received via RTC Datachannel: %s", str(message))

        # send pings
        asyncio.ensure_future(send_pings(f_channel))
    
    # ---------------------------------------------------------------------------------------------

    # get offer
    l_resp = requests.get(dfs.SIGNALING_SERVER_URL + "/get_offer")
    M_LOG.debug("l_resp: %s", str(l_resp.status_code))

    # ok ?
    if 200 == l_resp.status_code:
        # convert json
        l_data = l_resp.json()

        # offer ?
        if "offer" == l_data["type"]:
            # create session descriptor
            l_rd = RTCSessionDescription(sdp=l_data["sdp"], type=l_data["type"])

            # set remote description
            await l_peer_connection.setRemoteDescription(l_rd)
            # set local description
            await l_peer_connection.setLocalDescription(await l_peer_connection.createAnswer())
 
            # build message
            ldct_message = {"id": DS_ID, 
                            "sdp": l_peer_connection.localDescription.sdp, 
                            "type": l_peer_connection.localDescription.type}

            # send answer
            r = requests.post(dfs.SIGNALING_SERVER_URL + '/answer', data=ldct_message)
            M_LOG.info("message: %s", str(ldct_message))

            # forever...
            while True:
                # logger
                M_LOG.info("Ready for Stuff")
                # wait
                await asyncio.sleep(1)

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
