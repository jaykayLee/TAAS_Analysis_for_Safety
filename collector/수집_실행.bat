@echo off
chcp 65001 >nul
cd /d %~dp0
python -m taas_collector run --from 2005 --to 2025
python -m taas_collector status
python -m taas_collector export taas_raw_full.json.gz
pause
