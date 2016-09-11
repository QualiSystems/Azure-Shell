@echo off
call pack.bat
if %errorlevel% neq 0 exit /b %errorlevel%
call install.bat