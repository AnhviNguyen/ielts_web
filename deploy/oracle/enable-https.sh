#!/bin/bash
# Run on Oracle VM after certbot issued /etc/letsencrypt/live/linguaielts.site/
set -euo pipefail

cd ~/DATN

sudo mkdir -p /var/www/certbot/.well-known/acme-challenge
sudo chmod -R 755 /var/www/certbot

sudo apt-get update
sudo apt-get install -y nginx

sudo cp deploy/oracle/nginx-ssl.conf /etc/nginx/sites-available/linguaielts
sudo ln -sf /etc/nginx/sites-available/linguaielts /etc/nginx/sites-enabled/linguaielts
sudo rm -f /etc/nginx/sites-enabled/default

# Free :80/:443 for host nginx (Docker must not bind host port 80)
docker compose -f docker-compose.yml -f docker-compose.oracle.yml up -d gateway --force-recreate

sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

if ! sudo ss -tlnp | grep -q ':443'; then
  echo "ERROR: nothing listening on :443 — check: sudo journalctl -u nginx -n 20"
  exit 1
fi

echo ""
echo "OK — https://linguaielts.site should work now"
echo "Run: docker compose -f docker-compose.yml -f docker-compose.oracle.yml restart frontend api gateway"
