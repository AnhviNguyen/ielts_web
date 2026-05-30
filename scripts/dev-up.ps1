# Start stack with MailHog for local email testing
Set-Location $PSScriptRoot\..

if (-not (Test-Path .env)) {
    Copy-Item .env.production.example .env
    Write-Host "Created .env from .env.production.example — edit SECRET_KEY and DB_PASSWORD"
}

docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d --build

Write-Host ""
Write-Host "App:     http://localhost:8080"
Write-Host "MailHog: http://localhost:8025  (xem email reset password)"
Write-Host ""
Write-Host "Migration (first time):"
Write-Host "  docker compose exec api alembic upgrade head"
