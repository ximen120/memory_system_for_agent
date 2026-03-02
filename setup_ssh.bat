@echo off
chcp 65001 >nul
echo ==========================================
echo  配置SSH密钥 for GitHub & Gitee
echo ==========================================
echo.

set EMAIL=ffdd-120@163.com
set SSH_DIR=%USERPROFILE%\.ssh

:: 创建.ssh目录
if not exist "%SSH_DIR%" mkdir "%SSH_DIR%"

:: 生成SSH密钥
echo [1/4] 生成SSH密钥...
if exist "%SSH_DIR%\id_ed25519" (
    echo 密钥已存在，跳过生成
) else (
    ssh-keygen -t ed25519 -C "%EMAIL%" -f "%SSH_DIR%\id_ed25519" -N ""
    echo 密钥生成完成
)

echo.
echo [2/4] 启动SSH代理...
eval $(ssh-agent -s) 2>nul || ssh-agent

:: 添加密钥到代理
echo [3/4] 添加密钥到SSH代理...
ssh-add "%SSH_DIR%\id_ed25519" 2>nul

echo.
echo [4/4] 显示公钥内容...
echo ==========================================
echo 请复制下面的公钥内容，添加到GitHub和Gitee
echo ==========================================
type "%SSH_DIR%\id_ed25519.pub"
echo.
echo ==========================================
echo 添加地址：
echo GitHub: https://github.com/settings/keys
echo Gitee:  https://gitee.com/profile/sshkeys
echo ==========================================
echo.
echo 添加完成后，按任意键测试连接...
pause >nul

echo.
echo 测试GitHub连接...
ssh -T git@github.com

echo.
echo 测试Gitee连接...
ssh -T git@gitee.com

echo.
echo 配置完成！
pause
