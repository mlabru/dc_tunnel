#/bin/bash

# datachannel address
LS_TUNNEL_HOST="einstein"
LS_TUNNEL_HOST="localhost"
LI_TUNNEL_PORT=61001

# device address
# LS_TGT_HOST="localhost"
LI_TGT_PORT=50002

# client app address
# LS_CLI_HOST="localhost"
LI_CLI_PORT=50001

# start device app
# <target-port>
python3 tgt_app.py $LI_TGT_PORT > tgt_app.log &
sleep 2

# start datachannel target
# <datachannel-port> <target-port>
python3 sdk_tgt.py $LI_TUNNEL_PORT $LI_TGT_PORT > sdk_tgt.log 2> sdk_tgt.err &
sleep 2

# start datachannel client
# <datachannel-addr>:<datachannel-port> <client-port>
python3 sdk_cli.py $LS_TUNNEL_HOST:$LI_TUNNEL_PORT $LI_CLI_PORT > sdk_cli.log 2> sdk_cli.err &
sleep 2

# start client app
# <client-port>
python3 cli_app.py $LI_CLI_PORT > cli_app.log &
