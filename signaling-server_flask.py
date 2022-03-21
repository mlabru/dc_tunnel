# -*- coding: utf-8 -*-
"""
signaling-server_flask
signaling server made in Flask

2022/fev  1.0  mlabru   initial version (Linux/Python)
"""
# < imports >--------------------------------------------------------------------------------------

# python library
import json
import logging

# Flask
import flask

# .env
from dotenv import load_dotenv
    
# local
import sdk_def as dfs

# < defines >--------------------------------------------------------------------------------------
        
# logging level
# DI_LOG_LEVEL = logging.INFO

# < module data >----------------------------------------------------------------------------------

# logger
M_LOG = logging.getLogger(__name__)
M_LOG.setLevel(dfs.DI_LOG_LEVEL)

# -------------------------------------------------------------------------------------------------

# create Flask app
g_app = flask.Flask(__name__)

# data dictionary
gdct_data = {}

# -------------------------------------------------------------------------------------------------
@g_app.route("/answer", methods=["POST"])
def answer():
    """
    answer
    """
    # logger
    M_LOG.info("answer")

    if "answer" == flask.request.form["type"]:
        # save answer
        gdct_data["answer"] = {"id": flask.request.form["id"],
                               "type": flask.request.form["type"],
                               "sdp": flask.request.form["sdp"]}
        
        # return ok
        return flask.Response(status=200)

    # return
    return flask.Response(status=400)

# -------------------------------------------------------------------------------------------------
@g_app.route("/get_answer", methods=["GET"])
def get_answer():
    """
    get answer
    """
    # logger
    M_LOG.info("get_answer")

    # exist answer in dict ?
    if "answer" in gdct_data:
        # convert to JSON 
        l_json = json.dumps(gdct_data["answer"])

        # remove answer from dict
        del gdct_data["answer"]
        
        # return ok
        return flask.Response(l_json, status=200, mimetype="application/json")

    # return error
    return flask.Response(status=503)

# -------------------------------------------------------------------------------------------------
@g_app.route("/get_offer", methods=["GET"])
def get_offer():
    """
    get offer
    """
    # logger
    M_LOG.info("get_offer")

    # exist offer in dict ?
    if "offer" in gdct_data:
        # convert to JSON 
        l_json = json.dumps(gdct_data["offer"])

        # remove offer from dict
        del gdct_data["offer"]
        
        # return ok
        return flask.Response(l_json, status=200, mimetype="application/json")

    # return error
    return flask.Response(status=503)

# -------------------------------------------------------------------------------------------------
@g_app.route("/offer", methods=["POST"])
def offer():
    """
    offer
    """
    # logger
    M_LOG.info("offer")

    # request offer ?
    if "offer" == flask.request.form["type"]:
        # save offer
        gdct_data["offer"] = {"id": flask.request.form["id"],
                              "type": flask.request.form["type"],
                              "sdp": flask.request.form["sdp"]}
        
        # return ok
        return flask.Response(status=200)

    # return error
    return flask.Response(status=400)

# -------------------------------------------------------------------------------------------------
@g_app.route("/test")
def test():
    """
    test
    """
    # logger
    M_LOG.info("test")

    # return ok
    return flask.Response("{'status': 'ok'}", status=200, mimetype="application/json")

# -------------------------------------------------------------------------------------------------
# this is the bootstrap process
            
if "__main__" == __name__:
                
    # logger
    logging.basicConfig(level=dfs.DI_LOG_LEVEL)

    # disable logging
    # logging.disable(sys.maxint)

    # run application
    g_app.run(host="0.0.0.0", port=6969, debug=True)
    
# < the end >--------------------------------------------------------------------------------------
