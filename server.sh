#!/bin/bash

# Get local IP address
LOCAL_IP=$(grep -Po 'src \K.*(?= cache)' <<< $(ip route get 1))

# if RTNETLINK answers: Network is unreachable then use blank (localhost)

# Launch web server
python server/app.py $LOCAL_IP
