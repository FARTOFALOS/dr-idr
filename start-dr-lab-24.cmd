@echo off
rem DR Lab design 24 (Granicy hoda): the same start as DR Lab, then the page /24/ (the working screen since 2026-10-01; design 22 at /22/).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-dr-lab.ps1" -Page 24/ %*
