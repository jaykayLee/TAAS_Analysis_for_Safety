@echo off
chcp 65001 >nul
cd /d "%~dp0"
rem TAAS 교통사고 분석 — 시작 파일(생성물: _source/build/project_meta.py). 인자 없이 실행하면 프로젝트 홈을 엽니다.
if /i "%~1"=="online" (start "" "https://claude.ai/artifact/UaFGY49Midoyg6h7BVLune" & goto :eof)
if /i "%~1"=="home" goto home
if /i "%~1"=="main" goto main
if /i "%~1"=="serve" goto serve
if /i "%~1"=="update" goto update
if /i "%~1"=="sync" goto sync
if /i "%~1"=="build" goto build
if not "%~1"=="" goto help
:home
for %%f in ("%~dp001_Panel\Home\*.html") do (start "" "%%~ff" & goto :eof)
:main
for %%f in ("%~dp001_Panel\Main\*_offline.html") do (start "" "%%~ff" & goto :eof)
echo 메인 패널이 아직 없습니다 - 먼저 Main_TAAS.bat build 를 실행하세요.
pause
goto :eof
:serve
echo 로컬 서버로 메인 패널을 엽니다. 패널의 [업데이트] 버튼이 동작하며, 이 창을 닫으면 멈춥니다.
python _source\serve.py %2 %3
pause
goto :eof
:update
python _source\serve.py --update
pause
goto :eof
:sync
python _source\ops\pc_sync.py %2
pause
goto :eof
:build
python _source\build.py %2 %3 %4
if errorlevel 1 (echo. & echo 빌드 실패: install.bat 으로 의존성을 먼저 설치했는지 확인하세요.)
pause
goto :eof
:help
echo TAAS 교통사고 분석 시작 파일
echo   Main_TAAS.bat          프로젝트 홈(폴더 지도) - 여기서 메인 패널로
echo   Main_TAAS.bat main     메인 패널(오프라인판) 바로 열기
echo   Main_TAAS.bat serve    로컬 서버로 메인 패널 열기 - [업데이트] 버튼 동작
echo   Main_TAAS.bat update   최신 버전 받기 + 다시 만들기
echo   Main_TAAS.bat sync     바뀐 파일만 받기(pc_sync)
echo   Main_TAAS.bat build    라이브러리·패널 만들기(--full, --sample, --ext 부처)
echo   Main_TAAS.bat online   게시 패널(claude.ai) 열기
pause
