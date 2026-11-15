@echo off
chcp 65001 >nul
cd /d %~dp0
echo TAAS 패널을 엽니다. 이 창을 닫으면 패널의 [업데이트] 버튼이 동작하지 않습니다.
python serve.py %*
pause
