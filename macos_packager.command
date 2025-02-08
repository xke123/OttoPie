#!/bin/bash
cd "$(dirname "$0")"
source venv/bin/activate
python ottopie_packger.py
read -p "Press Enter to exit..."
