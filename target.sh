#/bin/bash

# device address
LS_TGT_HOST="localhost"
LI_TGT_PORT=50001

# datachannel address
LS_TUNNEL_HOST="localhost"
LI_TUNNEL_PORT=61001

# start device app
# <target-port>
python3 tgt_app.py $LI_TGT_PORT &

# start datachennel endpoint
# <datachannel-ip>:<datachannel-port> <target-ip>:<target-port>
python3 srv_sdk.py $LS_TUNNEL_HOST:$LI_TUNNEL_PORT $LS_TGT_HOST:$LI_TGT_PORT
