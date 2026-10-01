@echo off
rem DR Lab design 24 (Granicy hoda): the same start as DR Lab, then the page /24/ (design 22 stays at /).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-dr-lab.ps1" -Page 24/ %*
