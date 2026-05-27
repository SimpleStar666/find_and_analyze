@echo off
chcp 65001 >nul
setlocal

set PYTHON_DIR=%~dp0python
set WHEELS_DIR=%~dp0wheels
set SITE_PACKAGES=%PYTHON_DIR%\Lib\site-packages

if exist "%SITE_PACKAGES%\PyQt5" (
    echo 依赖已安装，跳过安装步骤
    goto :run
)

echo ============================================
echo   首次运行 - 正在安装依赖...
echo ============================================
echo.

echo [1/2] 安装 pip...
"%PYTHON_DIR%\python.exe" -m ensurepip --default-pip 2>nul
if errorlevel 1 (
    echo 正在下载 get-pip.py...
    curl -L -o "%~dp0get-pip.py" https://bootstrap.pypa.io/get-pip.py 2>nul
    if errorlevel 1 (
        echo 下载失败，尝试使用备用地址...
        curl -L -o "%~dp0get-pip.py" https://mirrors.huaweicloud.com/python/pip/get-pip.py 2>nul
    )
    "%PYTHON_DIR%\python.exe" "%~dp0get-pip.py" 2>nul
    del "%~dp0get-pip.py" 2>nul
)

echo.
echo [2/2] 安装依赖包...
"%PYTHON_DIR%\python.exe" -m pip install --no-index --find-links="%WHEELS_DIR%" PyQt5 requests openai -q 2>nul
if errorlevel 1 (
    echo 本地安装失败，尝试在线安装...
    "%PYTHON_DIR%\python.exe" -m pip install PyQt5 requests openai -i https://mirrors.huaweicloud.com/repository/pypi/simple/ -q
)

echo.
echo 安装完成！
echo.

:run
echo 正在启动 GitHub Repo Finder...
start "" "%PYTHON_DIR%\pythonw.exe" "%~dp0main.py"
