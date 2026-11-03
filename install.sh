#!/bin/bash
# Instala o uv (se necessário) e as dependências do projeto em .venv
# Uso: ./install.sh            -> só instala dependências
#      ./install.sh --service  -> instala também o serviço systemd (pede sudo)
set -euo pipefail

SCRIPT_DIR="$(dirname "$(realpath "$0")")"
cd "$SCRIPT_DIR"

export PATH="$HOME/.local/bin:$PATH"

if ! command -v uv >/dev/null 2>&1; then
    echo "Instalando uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
fi

# Cria .venv com a versão do Python de .python-version e instala versões fixadas no uv.lock
uv sync --frozen

if [[ "${1:-}" == "--service" ]]; then
    SERVICE=trajectory-orbit-propag
    UV_BIN="$(command -v uv)"
    sed -e "s|__USER__|$USER|g" \
        -e "s|__APP_DIR__|$SCRIPT_DIR|g" \
        -e "s|__UV__|$UV_BIN|g" \
        deploy/$SERVICE.service | sudo tee /etc/systemd/system/$SERVICE.service >/dev/null
    sudo systemctl daemon-reload
    sudo systemctl enable --now $SERVICE
    echo "Serviço instalado. Status: systemctl status $SERVICE | Logs: journalctl -u $SERVICE -f"
fi
