@echo off
chcp 65001 >nul
echo ==========================================
echo  记忆3.0 Agent Skills 安装脚本
echo ==========================================
echo.

set SOURCE_DIR=%~dp0skills
set TARGET_DIR=C:\Users\%USERNAME%\.stepfun\skills

echo 源目录: %SOURCE_DIR%
echo 目标目录: %TARGET_DIR%
echo.

if not exist "%TARGET_DIR%" (
    echo 创建目标目录...
    mkdir "%TARGET_DIR%"
)

echo [1/2] 安装 memory-system-3 skill...
if exist "%TARGET_DIR%\memory-system-3" (
    echo   已存在，跳过
) else (
    xcopy /E /I /Y "%SOURCE_DIR%\memory-system-3" "%TARGET_DIR%\memory-system-3"
    echo   安装成功
)

echo.
echo [2/2] 安装 memos-integration skill...
if exist "%TARGET_DIR%\memos-integration" (
    echo   已存在，跳过
) else (
    xcopy /E /I /Y "%SOURCE_DIR%\memos-integration" "%TARGET_DIR%\memos-integration"
    echo   安装成功
)

echo.
echo ==========================================
echo  安装完成！
echo ==========================================
echo.
echo 请重启AI助手以加载新skills
echo.
echo 已安装的skills:
echo   - memory-system-3
echo   - memos-integration
echo.
pause
