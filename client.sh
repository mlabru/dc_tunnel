#/bin/bash

# client app address
LS_CLI_HOST="localhost"
LI_CLI_PORT=50002

# datachannel address
LS_TUNNEL_HOST="localhost"
LI_TUNNEL_PORT=61001

# start datachennel endpoint
# <datachannel-port> <client-port>
python3 cli_sdk.py $LI_TUNNEL_PORT $LI_CLI_PORT &

# start client app
# <client-port>
python3 cli_app.py $LI_CLI_PORT
