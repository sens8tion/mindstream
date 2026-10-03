@echo off
setlocal
rem the Forge environment: MINDSTREAM_PYTHON, else "forge_python" / "forge_dir" in models.local.json, else plain python
if not defined MINDSTREAM_PYTHON for /f "delims=" %%p in ('python -B "%~dp0..\mindstream\local.py" forge_python') do set "MINDSTREAM_PYTHON=%%p"
if not defined MINDSTREAM_PYTHON set "MINDSTREAM_PYTHON=python"
"%MINDSTREAM_PYTHON%" -B -W ignore "%~dp0..\img_gen.py" %*
