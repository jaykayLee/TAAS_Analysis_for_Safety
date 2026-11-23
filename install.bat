@echo off
chcp 65001 >nul
setlocal EnableExtensions EnableDelayedExpansion
title TAAS 교통사고 분석 — 의존성 설치
cd /d "%~dp0"
set "DEP=%~dp002_Strategy\05_Dependencies"
set RESTART=0
set FAIL=0
rem 자동 생성(_source/build/template/deps.py, 원천 _source/build/deps.json) — 목록은 02_Strategy\05_Dependencies\의존성_목록_v1.0.docx
echo ============================================================
echo  TAAS 교통사고 분석 — 의존성 설치(빌드용). 보기만 할 때는 설치할 것이 없습니다.
echo ============================================================
echo.
echo  B = 빌드용 설치 + 확인      V = 확인만(글꼴 · 실제 Office로 파일 열기 시험 — 보기만 하는 사람도 권장)
choice /c BV /m "  선택"
if errorlevel 2 (set "MODE=V" & goto :verify)
set "MODE=B"
echo.
echo [1/5] 도구 확인
call :tool python "Python" "Python.Python.3.12" "필수" "https://www.python.org/downloads/"
call :tool node "Node.js" "OpenJS.NodeJS.LTS" "필수" "https://nodejs.org/"
call :tool git "Git (Git Bash 포함)" "Git.Git" "필수" "https://git-scm.com/"
call :tool pandoc "pandoc" "JohnMacFarlane.Pandoc" "필수" "https://pandoc.org/installing.html"
if "%RESTART%"=="1" (
  echo.
  echo 새로 설치한 도구가 PATH에 반영되도록 이 창을 닫고 install.bat을 다시 실행하세요.
  pause
  exit /b 0
)
echo.
echo [2/5] Python 패키지 — %DEP%\requirements.txt
python -m pip install --upgrade pip
python -m pip install -r "%DEP%\requirements.txt" || set FAIL=1
echo.
echo [3/5] Node 패키지(전역) — %DEP%\npm-packages.txt
for /f "usebackq eol=# tokens=1" %%p in ("%DEP%\npm-packages.txt") do (call npm install -g "%%p" || set FAIL=1)
for /f "delims=" %%r in ('npm root -g') do (setx NODE_PATH "%%r" >nul & set "NODE_PATH=%%r" & echo   NODE_PATH=%%r ^(전역 패키지를 require 할 수 있게^))
echo.
echo [4/5] 후속 설치
echo.
echo 확인:
python -c "import sys; print('  Python', sys.version.split()[0])"
python -c "import pandas, pyarrow, duckdb, openpyxl, docx, playwright, statsmodels, pymannkendall; print('  Python 패키지 OK')" || set FAIL=1
node -e "require('pptxgenjs');console.log('  Node 패키지 OK')" || set FAIL=1
if exist "%USERPROFILE%\.bashrc" (findstr /c:"alias python3=python" "%USERPROFILE%\.bashrc" >nul || echo alias python3=python>>"%USERPROFILE%\.bashrc") else (echo alias python3=python>"%USERPROFILE%\.bashrc")
echo   Git Bash: python3 별칭 확인(.bashrc)
:verify
echo.
echo [5/5] Windows 확인 — 글꼴 · PowerPoint·Word·Excel로 열기 시험(02_Strategy\05_Dependencies\verify_office.ps1)
powershell -NoProfile -ExecutionPolicy Bypass -File "%DEP%\verify_office.ps1"
if errorlevel 1 set FAIL=1
echo.
if "%FAIL%"=="1" (echo 일부 단계가 실패했습니다 — 위 메시지와 02_Strategy\05_Dependencies\office_verify_report.txt · 의존성 목록 문서를 확인하세요.) else if "%MODE%"=="V" (echo 확인 끝 — 결과는 위 화면과 02_Strategy\05_Dependencies\office_verify_report.txt) else (echo 설치·확인 완료 — Git Bash에서: cd _source ^&^& bash build/build_release.sh)
pause
exit /b 0

:tool
rem %1=id %2=이름 %3=winget ID %4=필수/선택 %5=URL
set "FOUND=" & set "NM=%~2"
if /i "%~1"=="python" (
  python -c "import sys" >nul 2>nul && set "FOUND=1"
) else if /i "%~1"=="libreoffice" (
  where soffice >nul 2>nul && set "FOUND=1"
  if exist "%ProgramFiles%\LibreOffice\program\soffice.exe" set "FOUND=1"
) else (
  where %~1 >nul 2>nul && set "FOUND=1"
)
if defined FOUND (
  echo   [있음] !NM!
  goto :eof
)
echo   [없음] !NM! - %~4
where winget >nul 2>nul
if errorlevel 1 (
  echo     winget이 없습니다 - 직접 설치: %~5
  if /i "%~4"=="필수" set FAIL=1
  goto :eof
)
choice /c YN /m "    winget으로 !NM! 설치할까요"
if errorlevel 2 (
  if /i "%~4"=="필수" set FAIL=1
  goto :eof
)
winget install -e --id %~3 --accept-source-agreements --accept-package-agreements && set RESTART=1
goto :eof
