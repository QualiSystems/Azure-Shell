@echo off
rem run_packager.bat
cd package
\Python27\python.exe setup.py sdist
cd..