#!/bin/bash

# Obter o caminho absoluto do script
SCRIPT_PATH="$(realpath "$0")"

# Obter o diretório do script
SCRIPT_DIR="$(dirname "$SCRIPT_PATH")"

cd "$SCRIPT_DIR"

# Cria um novo ambiente virtual chamado 'env'
# virtualenv env
python3 -m venv env 

# Ativa o ambiente virtual
source env/bin/activate
# Atualiza o pip para a versão mais recente
pip install --upgrade pip
# Instala as dependências do arquivo requirements.txt
pip install -r requirements.txt