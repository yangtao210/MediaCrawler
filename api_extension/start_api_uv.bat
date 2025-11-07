@echo off
chcp 65001 >nul
REM MediaCrawler API 一键启动脚本（UV虚拟环境）

echo ========================================
echo MediaCrawler API 启动脚本（UV环境）
echo ========================================
echo.

REM 切换到项目根目录
cd /d "%~dp0\.."

REM 检查UV
uv --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到UV，请先安装UV
    pause
    exit /b 1
)

echo [信息] 检测到UV版本:
uv --version
echo.

REM 同步依赖
echo [信息] 正在同步项目依赖...
uv sync
if %errorlevel% neq 0 (
    echo [错误] 依赖同步失败
    pause
    exit /b 1
)

echo.
echo [成功] 所有依赖检查完成！
echo.
echo ========================================
echo 正在启动 MediaCrawler API 服务...
echo ========================================
echo.
echo API服务地址: http://localhost:8000
echo API文档地址: http://localhost:8000/docs
echo.
echo 按 Ctrl+C 可以停止服务
echo ========================================
echo.

REM 启动API服务
uv run python api_extension\api_server.py

pause

