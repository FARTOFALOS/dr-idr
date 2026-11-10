@echo off
rem DR Lab 23.5 - cells: the same 23.5 server (port 8735) opened with the layer "cells" on: the family's joint table
rem (15 minutes x 0.1 SD) drawn as it is, no zones (operator 30.10). The desktop shortcut "DR Lab 23.5 - cells" points here.
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-dr-lab-23-5.ps1" -Page "23-5/#cells=1" %*
