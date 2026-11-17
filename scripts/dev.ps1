$ErrorActionPreference = "Stop"
Set-Location (Split-Path -Parent $PSScriptRoot)

if (-not (Test-Path ".env")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created .env from .env.example — rotate FERNET_KEY before storing real credentials."
}

docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build @args
