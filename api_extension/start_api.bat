@echo off
chcp 65001 >nul
REM MediaCrawler API 一键启动脚本（原生环境）

echo ========================================
echo MediaCrawler API 启动脚本（原生环境）
echo ========================================
echo.

REM 切换到项目根目录
cd /d "%~dp0\.."

REM 检查Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [错误] 未检测到Python，请先安装Python 3.9或更高版本
    pause
    exit /b 1
)

echo [信息] 检测到Python版本:
python --version
echo.

REM 检查依赖
echo [信息] 检查项目依赖...
python -c "import fastapi" >nul 2>&1
if %errorlevel% neq 0 (
    echo [警告] 检测到缺少依赖包，正在安装...
    pip install -r requirements.txt
    if %errorlevel% neq 0 (
        echo [错误] 依赖安装失败
        pause
        exit /b 1
    )
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
python api_extension\api_server.py

pause

