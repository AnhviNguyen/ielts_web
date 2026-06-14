#!/bin/sh
set -e

if [ -z "$BACKEND_INTERNAL_URL" ]; then
  echo "ERROR: BACKEND_INTERNAL_URL is required." >&2
  echo "  Example (Railway private networking): http://<api-service>.railway.internal:7860" >&2
  exit 1
fi

# Strip trailing slash so proxy_pass URLs stay well-formed.
BACKEND_INTERNAL_URL="${BACKEND_INTERNAL_URL%/}"
export BACKEND_INTERNAL_URL

envsubst '${BACKEND_INTERNAL_URL}' \
  < /etc/nginx/templates/default.conf.template \
  > /etc/nginx/conf.d/default.conf

exec nginx -g 'daemon off;'
