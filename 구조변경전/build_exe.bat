@echo off
echo ========================================
echo 통합관리시스템 EXE 빌드 시작
echo ========================================

REM 기존 빌드 파일 정리
if exist "build" rmdir /s /q build
if exist "dist" rmdir /s /q dist
if exist "*.spec" del /q *.spec

echo 빌드 파일 정리 완료...

REM PyInstaller로 EXE 빌드
echo EXE 빌드 중...
pyinstaller --onefile --windowed --name="통합관리시스템" ^
    --add-data "config;config" ^
    --add-data "data;data" ^
    --hidden-import="src.features.keyword_analysis" ^
    --hidden-import="src.features.powerlink_analyzer" ^
    --hidden-import="src.features.rank_tracking" ^
    --hidden-import="src.features.naver_cafe" ^
    main.py

if %ERRORLEVEL% NEQ 0 (
    echo 빌드 실패!
    pause
    exit /b 1
)

echo ========================================
echo 빌드 완료! 
echo 파일 위치: dist\통합관리시스템.exe
echo ========================================
pause