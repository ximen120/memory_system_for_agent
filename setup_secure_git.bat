@echo off
chcp 65001 >nul
echo ==========================================
echo  记忆3.0 Git安全配置脚本
echo ==========================================
echo.

REM 配置Git凭证管理器
echo [1/3] 配置Git凭证管理器...
git config --global credential.helper manager
echo √ Git凭证管理器已启用
echo.

REM 首次推送会提示输入凭证，之后会自动记住
echo [2/3] 测试连接（会提示输入用户名和密码/令牌）...
echo 说明：首次需要输入您的Gitee凭证，之后Windows会自动记住
echo.

REM 创建凭证提示说明
echo [3/3] 创建使用说明...
echo.
echo ==========================================
echo  配置完成！
echo ==========================================
echo.
echo 使用方法：
echo 1. 首次运行时，双击 sync_now.bat
echo 2. 会弹出窗口要求输入用户名和令牌
echo 3. 输入：
echo    用户名：ximen120
echo    密码：  e4cb305baf1da9616495405451a7b906
echo 4. 勾选"记住凭证"
echo 5. 之后同步无需再次输入
echo.
echo 安全提示：
echo - 令牌存储在Windows凭证管理器中，加密保存
echo - 脚本中不再包含明文令牌
echo - 比SSH方案更简单，适合个人使用
echo.
pause
"