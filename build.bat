@echo off
title "start building"
uv run -m nuitka --standalone --windows-disable-console --remove-output -o "te_tube.exe" main.py
xcopy "lib" "main.dist/lib" /E /I /Y
cls
title "Build successful"
pause