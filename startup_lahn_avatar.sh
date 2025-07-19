#!/bin/bash

# Backend
screen -L -Logfile ~/backend-logs.0 -dmS backend bash -c 'cd ~/Lahn-Avatar && source lahn_env/bin/activate && python server.py'

# Frontend
screen -L -Logfile ~/frontend-logs.0 -dmS frontend bash -c 'cd ~/Lahn-Avatar/frontend && npm run dev'

# Caddy
screen -dmS caddy bash -c 'cd ~/caddy-related && caddy run'
