@echo off
rem DR Lab 24 (15.11.2026): 23.5 with the price column R9, branch ekran-24-r9, its own port 8741 (23.5 on 8767 is never touched).
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0start-dr-lab-24.ps1" %*
