@echo off
copy version.txt package/version.txt
copy version.txt drivers/version.txt
pushd %CD%
cd drivers 
call pack.bat
popd
