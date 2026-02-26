@echo off
chcp 65001 >nul
echo 正在同步记忆3.0项目到Gitee...
cd /d "%~dp0"
python auto_sync.py
echo.
echo 同步完成！
pause
