#!/bin/bash

# Get local IP address
LOCAL_IP=$(grep -Po 'src \K.*(?= cache)' <<< $(ip route get 1))

# if RTNETLINK answers: Network is unreachable then use blank (localhost)
SIZE=${#LOCAL_IP}

# Launch web server
if [ $SIZE = 0 ]; then
    python server/app.py ""
else
    python server/app.py $LOCAL_IP
fi
