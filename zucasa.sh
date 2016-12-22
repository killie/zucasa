#!/bin/bash

# Get local IP address
LOCAL_IP=$(grep -Po 'src \K.*(?= cache)' <<< $(ip route get 1))
SIZE=${#LOCAL_IP}

if [ $SIZE = 0 ]; then
    # if RTNETLINK answers: Network is unreachable then use blank (localhost)
    python server/app.py ""
else
    # Launch web server
    python server/app.py $LOCAL_IP
fi
