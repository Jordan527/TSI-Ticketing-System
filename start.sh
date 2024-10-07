#!/bin/bash

ngrok config add-authtoken $NGROK_TOKEN

ngrok http --domain=$NGROK_DOMAIN 5000 &
flask run --host=0.0.0.0 --port=5000 &

while ! curl -s http://localhost:5000/health > /dev/null; do
    sleep 1
done

curl -X POST http://localhost:5000/initialise || true

wait