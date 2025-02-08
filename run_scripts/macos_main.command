#!/bin/bash
cd "$(dirname "$0")"
if [ ! -d "../venv" ]; then
    echo "解压 venv.zip..."
    unzip -q ../venv.zip -d ..
fi
source ../venv/bin/activate
python ../main.py
read -p "Press Enter to exit..."
