#!/bin/bash

BACKEND=avatar-garden-backend
FRONTEND_DIR=/root/AvatarGarden/frontend
WEBROOT=/var/www/avatar-garden

usage() {
  echo "Usage: avatars.sh [command]"
  echo ""
  echo "Commands:"
  echo "  start|stop|restart    Backend service"
  echo "  status                Show backend status"
  echo "  logs                  Tail backend log (Ctrl+C to exit)"
  echo "  deploy                Build frontend (mac mode) and deploy to $WEBROOT"
  echo "  -h|--help             This help"
}

case "$1" in
  start|stop|restart)
    systemctl $1 $BACKEND
    [ "$1" != "stop" ] && systemctl status $BACKEND --no-pager | grep -E "Active|●|Main PID"
    ;;
  status)
    systemctl status $BACKEND --no-pager | grep -E "Active|●|Main PID"
    ;;
  logs)
    tail -f /root/AvatarGarden/backend_log.0
    ;;
  deploy)
    set -e
    cd $FRONTEND_DIR
    npm run build -- --mode mac
    rsync -a --delete $FRONTEND_DIR/dist/ $WEBROOT/
    echo "Deployed to $WEBROOT"
    ;;
  -h|--help)
    usage
    ;;
  *)
    usage
    ;;
esac