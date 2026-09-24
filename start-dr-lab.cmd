@echo off
rem DR Lab: double-click to start (TradingView with the candle channel, the local server, the page).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-dr-lab.ps1" %*
