@echo off
setlocal
rem the project's own environment (.venv-dml beside the code), or MINDSTREAM_DML_PYTHON, or plain python
if not defined MINDSTREAM_DML_PYTHON set "MINDSTREAM_DML_PYTHON=%~dp0..\.venv-dml\Scripts\python.exe"
if not exist "%MINDSTREAM_DML_PYTHON%" set "MINDSTREAM_DML_PYTHON=python"
"%MINDSTREAM_DML_PYTHON%" -B -W ignore "%~dp0..\te_amd.py" export %*
