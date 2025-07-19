#!/bin/bash

# Backend
screen -L -Logfile ~/backend-logs.0 -dmS backend bash -c 'cd ~/Lahn-Avatar && source lahn_env/bin/activate && python3 server.py'

# Frontend
screen -L -Logfile ~/frontend-logs.0 -dmS frontend bash -c 'cd ~/Lahn-Avatar/frontend && npm run dev'

# Caddy
sudo setcap 'cap_net_bind_service=+ep' /usr/bin/caddy
screen -dmS caddy bash -c 'cd ~/caddy-related && caddy run'
