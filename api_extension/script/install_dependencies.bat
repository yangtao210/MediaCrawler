@echo off
chcp 65001 >nul
REM MediaCrawler 依赖安装脚本（原生环境）

echo ========================================
echo MediaCrawler 依赖安装脚本
echo ========================================
echo.

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python
    pause
    exit /b 1
)

echo [信息] Python版本:
python --version
echo.

REM 安装Python依赖
echo [步骤 1/2] 安装Python依赖包...
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo [错误] 依赖安装失败
    pause
    exit /b 1
)

echo.
echo [步骤 2/2] 安装浏览器驱动...
playwright install chromium
if %errorlevel% neq 0 (
    echo [错误] 浏览器驱动安装失败
    pause
    exit /b 1
)

echo.
echo ========================================
echo [成功] 所有依赖安装完成！
echo ========================================
echo.
echo 现在您可以运行 start_api.bat 来启动API服务
echo.

pause

