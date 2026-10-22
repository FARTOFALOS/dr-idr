@echo off
rem DR Lab 23.5: the successor candidate of screen 24 on its own port 8735 (screen 24 on 8767 is never touched).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-dr-lab-23-5.ps1" %*
