@echo off
pushd %~dp0
call .\.venv\Scripts\activate
python unibot.py
popd
pause
