@echo off
chcp 65001 >nul
REM MediaCrawler 依赖安装脚本（UV环境）

echo ========================================
echo MediaCrawler 依赖安装脚本（UV环境）
echo ========================================
echo.

REM 检查UV
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到UV，请先安装UV
    echo 安装方法: pip install uv
    pause
    exit /b 1
)

echo [信息] UV版本:
uv --version
echo.

REM 同步依赖
echo [步骤 1/2] 同步项目依赖...
uv sync
if %errorlevel% neq 0 (
    echo [错误] 依赖同步失败
    pause
    exit /b 1
)

echo.
echo [步骤 2/2] 安装浏览器驱动...
uv run playwright install chromium
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
echo 现在您可以运行 start_api_uv.bat 来启动API服务
echo.

pause

