@echo off
cd /d "%~dp0"
call venv\Scripts\activate
python ottopie_packger.py
pause
