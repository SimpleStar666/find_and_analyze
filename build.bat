@echo off
chcp 65001 >nul
echo ============================================
echo   GitHub Repo Finder - Windows 打包脚本
echo ============================================
echo.

echo [1/3] 检查 Python 环境...
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误：未找到 Python！请先安装 Python 3.8+
    echo 下载地址：https://www.python.org/downloads/
    echo 安装时请勾选 "Add Python to PATH"
    pause
    exit /b 1
)
echo Python 环境检查通过

echo.
echo [2/3] 安装依赖...
pip install -r requirements.txt -q
if errorlevel 1 (
    echo 错误：依赖安装失败！
    pause
    exit /b 1
)
echo 依赖安装完成

echo.
echo [3/3] 开始打包...
pyinstaller --clean --noconfirm GitHubRepoFinder.spec
if errorlevel 1 (
    echo 错误：打包失败！
    pause
    exit /b 1
)

echo.
echo ============================================
echo   打包成功！
echo   可执行文件位置：dist\GitHubRepoFinder.exe
echo ============================================
echo.
echo 你可以将 dist\GitHubRepoFinder.exe 复制到任何位置运行
echo 导出的报告会保存在 exe 同级目录的 output 文件夹中
echo.
pause
