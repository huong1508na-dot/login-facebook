@echo off
setlocal
title Build Facebook Cookie Login EXE
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python chua duoc cai hoac chua co trong PATH.
  pause
  exit /b 1
)

echo [1/3] Cai thu vien...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt pyinstaller
if errorlevel 1 goto :error

echo.
echo [2/3] Don ban build cu...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist FacebookCookieLogin.spec del /q FacebookCookieLogin.spec

echo.
echo [3/3] Build file EXE...
python -m PyInstaller ^
  --noconfirm ^
  --clean ^
  --onefile ^
  --noconsole ^
  --name FacebookCookieLogin ^
  --collect-all customtkinter ^
  main.py

if errorlevel 1 goto :error

echo.
echo ==========================================
echo BUILD THANH CONG
echo File: dist\FacebookCookieLogin.exe
echo ==========================================
start "" "%~dp0dist"
pause
exit /b 0

:error
echo.
echo [ERROR] Build that bai.
pause
exit /b 1
