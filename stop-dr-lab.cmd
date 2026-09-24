@echo off
rem DR Lab: stop the local server (TradingView is left running).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0stop-dr-lab.ps1"
