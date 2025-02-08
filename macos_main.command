#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python main.py
read -p "Press Enter to exit..."
