@echo off
setlocal
rem the ComfyUI environment: MINDSTREAM_COMFY_PYTHON, else "comfy_python" / "comfy_dir" in models.local.json, else plain python
if not defined MINDSTREAM_COMFY_PYTHON for /f "delims=" %%p in ('python -B "%~dp0..\mindstream\local.py" comfy_python') do set "MINDSTREAM_COMFY_PYTHON=%%p"
if not defined MINDSTREAM_COMFY_PYTHON set "MINDSTREAM_COMFY_PYTHON=python"
"%MINDSTREAM_COMFY_PYTHON%" -B -W ignore "%~dp0..\vid_gen.py" %*
