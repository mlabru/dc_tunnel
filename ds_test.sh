#/bin/bash

# datachannel address
LS_TUNNEL_HOST="localhost"
LI_TUNNEL_PORT=61001

# device address
LS_TGT_HOST="localhost"
LI_TGT_PORT=50002

# client app address
LS_CLI_HOST="localhost"
LI_CLI_PORT=50001

# start datachennel client
# <datachannel-port> <client-port>
python3 cli_sdk.py $LI_TUNNEL_PORT $LI_CLI_PORT &
sleep 2

# start device app
# <target-port>
python3 tgt_app.py $LI_TGT_PORT &
sleep 2

# start datachennel endpoint
# <datachannel-ip>:<datachannel-port> <target-ip>:<target-port>
python3 srv_sdk.py $LS_TUNNEL_HOST:$LI_TUNNEL_PORT $LS_TGT_HOST:$LI_TGT_PORT &
sleep 2

# start client app
# <client-port>
python3 cli_app.py $LI_CLI_PORT &
