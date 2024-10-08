#!/bin/bash

ngrok config add-authtoken $NGROK_TOKEN

# Start the server
ngrok http --domain=$NGROK_DOMAIN 5000 &
flask run --host=0.0.0.0 --port=5000 &

# Wait for the server to start
count=0
while [ $count -lt 10 ]; do
  curl -s POST http://localhost:5000/health && break
  count=$((count + 1))
  sleep 2
done

# Initialise the server
curl -X POST http://localhost:5000/initialise || true

wait