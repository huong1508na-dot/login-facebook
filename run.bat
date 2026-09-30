@echo off
title Facebook Cookie Login
cd /d "%~dp0"

where python >nul 2>nul
if errorlevel 1 (
  echo [ERROR] Python chua duoc cai hoac chua co trong PATH.
  echo Tai Python tu python.org va tick Add Python to PATH khi cai.
  pause
  exit /b 1
)

echo Dang cai/kiem tra thu vien...
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo.
  echo [ERROR] Khong cai duoc thu vien.
  pause
  exit /b 1
)

echo.
echo Dang mo ung dung...
python main.py

if errorlevel 1 (
  echo.
  echo Ung dung da dung voi loi.
  pause
)
