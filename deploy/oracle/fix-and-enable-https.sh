#!/bin/bash
# Fix broken gateway ports + free :80 for host nginx. Run on Oracle VM.
set -euo pipefail
cd ~/DATN

echo "==> Stop Docker gateway (free port 80)"
docker stop datn-gateway-1 2>/dev/null || true

echo "==> Fix docker-compose.yml gateway ports -> 8080:80 only"
python3 << 'PY'
from pathlib import Path
path = Path("docker-compose.yml")
lines = path.read_text().splitlines()
out = []
i = 0
while i < len(lines):
    line = lines[i]
    out.append(line)
    if line == "  gateway:":
        i += 1
        while i < len(lines):
            cur = lines[i]
            if cur.startswith("  ") and not cur.startswith("    "):
                break
            if cur.strip() == "ports:":
                out.append(cur)
                i += 1
                while i < len(lines) and lines[i].startswith("      - "):
                    i += 1
                out.append('      - "8080:80"')
                continue
            out.append(cur)
            i += 1
        continue
    i += 1
path.write_text("\n".join(out) + "\n")
print("gateway ports:", [l for l in out if "8080" in l or (l.strip() == "ports:")])
PY

echo "==> Validate compose"
docker compose config >/dev/null

echo "==> Start host nginx (HTTPS :443)"
sudo cp deploy/oracle/nginx-ssl.conf /etc/nginx/sites-available/linguaielts
sudo ln -sf /etc/nginx/sites-available/linguaielts /etc/nginx/sites-enabled/linguaielts
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t
sudo systemctl enable nginx
sudo systemctl restart nginx

echo "==> Start Docker gateway on :8080"
docker compose up -d gateway --force-recreate

echo "==> Ports"
sudo ss -tlnp | grep -E ':80|:443|:8080' || true

echo ""
echo "Done. Test: https://linguaielts.site"
