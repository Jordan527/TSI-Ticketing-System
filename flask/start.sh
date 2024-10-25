#!/bin/bash

ngrok config add-authtoken $NGROK_TOKEN

# Start the server
ngrok http --domain=$NGROK_DOMAIN 5000 &
flask run --host=0.0.0.0 --port=5000