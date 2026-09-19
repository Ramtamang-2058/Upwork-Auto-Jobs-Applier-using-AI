#!/bin/bash
# Deploy the cover-letter API to a remote server over SSH.
#
# Usage:
#   VPS_IP=203.0.113.10 VPS_USER=root ./deploy.sh
#
# All values can be supplied via environment variables; nothing is hardcoded.
set -e

VPS_IP="${VPS_IP:?Set VPS_IP to your server address}"
VPS_USER="${VPS_USER:-root}"
REMOTE_DIR="${REMOTE_DIR:-/opt/upwork-api}"
IMAGE_NAME="${IMAGE_NAME:-upwork-cover-letter-api}"

echo "================================================================================"
echo "  DEPLOYING UPWORK COVER LETTER API TO $VPS_USER@$VPS_IP"
echo "================================================================================"

echo ""
echo "1) Testing SSH connection..."
if ! ssh -o ConnectTimeout=5 "$VPS_USER@$VPS_IP" "echo OK"; then
    echo "   Cannot connect to $VPS_USER@$VPS_IP" >&2
    exit 1
fi

echo ""
echo "2) Creating deployment package..."
tar -czf deploy-package.tar.gz \
    --exclude='venv' \
    --exclude='.venv' \
    --exclude='node_modules' \
    --exclude='__pycache__' \
    --exclude='*.pyc' \
    --exclude='.git' \
    --exclude='debug_*' \
    --exclude='tests' \
    --exclude='electron-app' \
    --exclude='chrome-extension' \
    --exclude='.env' \
    Dockerfile \
    docker-compose.yml \
    requirements.txt \
    server.py \
    src/ \
    files/

echo ""
echo "3) Uploading package..."
scp deploy-package.tar.gz "$VPS_USER@$VPS_IP:/tmp/"

echo ""
echo "4) Deploying on server..."
ssh "$VPS_USER@$VPS_IP" << 'ENDSSH'
set -e

mkdir -p /opt/upwork-api
cd /opt/upwork-api
tar -xzf /tmp/deploy-package.tar.gz
rm /tmp/deploy-package.tar.gz

if ! command -v docker &> /dev/null; then
    echo "Installing Docker..."
    curl -fsSL https://get.docker.com -o get-docker.sh
    sh get-docker.sh
    systemctl start docker
    systemctl enable docker
    rm get-docker.sh
fi

# Environment file: create from .env.example if it does not exist
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env from .env.example - add your API keys, then re-run."
fi

docker stop upwork-api 2>/dev/null || true
docker rm upwork-api 2>/dev/null || true

docker build -t upwork-cover-letter-api:latest .
docker run -d \
    --name upwork-api \
    --restart unless-stopped \
    -p 5000:5000 \
    --env-file .env \
    upwork-cover-letter-api:latest

sleep 5
docker ps | grep upwork-api || true
ENDSSH

echo ""
echo "5) Testing API endpoint..."
sleep 2
if curl -fsS "http://$VPS_IP:5000/health"; then
    echo ""
    echo "OK - API is responding."
else
    echo "Warning: API not responding yet (give it a few more seconds)."
fi

rm -f deploy-package.tar.gz

echo ""
echo "================================================================================"
echo "  DEPLOYMENT COMPLETE"
echo "  API:  http://$VPS_IP:5000"
echo "  Logs: ssh $VPS_USER@$VPS_IP 'docker logs upwork-api -f'"
echo "================================================================================"