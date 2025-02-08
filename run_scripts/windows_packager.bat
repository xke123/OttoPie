@echo off
cd /d "%~dp0"
if not exist "..\venv" (
    echo 解压 venv.zip...
    powershell -Command "Expand-Archive -Path ..\venv.zip -DestinationPath ..\"
)
call ..\venv\Scripts\activate
python ..\ottopie_packger.py
pause
