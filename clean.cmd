@echo off
pushd "%~dp0"

rmdir /s /q build 2>nul
rmdir /s /q dist 2>nul
rmdir /s /q fitdecode.egg-info 2>nul

rmdir /s /q fitdecode\__pycache__ 2>nul
rmdir /s /q fitdecode\cmd\__pycache__ 2>nul

rmdir /s /q tests\__pycache__ 2>nul

popd
