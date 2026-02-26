@echo off
chcp 65001 >nul
echo 🧠 正在启动记忆系统...
C:\Users\Simon\.conda\envs\memory_v3\python.exe D:\wordir\memory_system_v3\memory_boot.py
if %errorlevel% == 0 (
    echo.
    echo ✅ 记忆系统已就绪
    echo 💡 提示: 现在可以在Python中使用记忆功能
) else (
    echo ❌ 启动失败
)
pause
