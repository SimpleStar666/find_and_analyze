@echo off
chcp 65001 >nul
setlocal EnableDelayedExpansion

set "BASE_DIR=%~dp0"
set "PYTHON_DIR=%BASE_DIR%python"
set "WHEELS_DIR=%BASE_DIR%wheels"
set "SITE_PACKAGES=%PYTHON_DIR%\Lib\site-packages"
set "PYTHON_EXE=%PYTHON_DIR%\python.exe"
set "PYTHONW_EXE=%PYTHON_DIR%\pythonw.exe"
set "MAIN_PY=%BASE_DIR%main.py"

echo ============================================
echo   GitHub Repo Finder 启动器
echo ============================================
echo.
echo 应用目录: %BASE_DIR%
echo Python目录: %PYTHON_DIR%
echo.

if not exist "%PYTHON_EXE%" (
    echo [错误] 找不到 python.exe
    echo 期望路径: %PYTHON_EXE%
    echo 请确认 python 文件夹在 bat 文件同级目录下
    echo.
    pause
    exit /b 1
)

if not exist "%MAIN_PY%" (
    echo [错误] 找不到 main.py
    echo 期望路径: %MAIN_PY%
    echo.
    pause
    exit /b 1
)

echo [检查] python.exe ... 存在
echo [检查] main.py ... 存在

if exist "%SITE_PACKAGES%\PyQt5" (
    echo [检查] PyQt5 依赖 ... 已安装
    goto :run
)

echo.
echo [提示] 首次运行，需要安装依赖包...
echo.

echo [1/2] 安装 pip...
"%PYTHON_EXE%" -m ensurepip --default-pip
if errorlevel 1 (
    echo ensurepip 失败，尝试下载 get-pip.py...
    curl -L -o "%BASE_DIR%get-pip.py" https://bootstrap.pypa.io/get-pip.py
    if errorlevel 1 (
        echo 下载失败，尝试备用地址...
        curl -L -o "%BASE_DIR%get-pip.py" https://mirrors.huaweicloud.com/python/pip/get-pip.py
    )
    "%PYTHON_EXE%" "%BASE_DIR%get-pip.py"
    del "%BASE_DIR%get-pip.py" 2>nul
)

echo.
echo [2/2] 安装依赖包（PyQt5, requests, openai）...
echo 这可能需要几分钟，请耐心等待...
echo.

if exist "%WHEELS_DIR%\PyQt5-5.15.10-cp37-abi3-win_amd64.whl" (
    echo 使用本地 wheel 文件安装...
    "%PYTHON_EXE%" -m pip install --no-index --find-links="%WHEELS_DIR%" PyQt5 requests openai
) else (
    echo 本地 wheel 不存在，在线安装...
    "%PYTHON_EXE%" -m pip install PyQt5 requests openai -i https://mirrors.huaweicloud.com/repository/pypi/simple/
)

if errorlevel 1 (
    echo.
    echo [错误] 依赖安装失败！
    echo 请检查网络连接后重试
    echo.
    pause
    exit /b 1
)

echo.
echo 依赖安装完成！
echo.

:run
echo.
echo 正在启动 GitHub Repo Finder...
echo.

cd /d "%BASE_DIR%"

if exist "%PYTHONW_EXE%" (
    start "" "%PYTHONW_EXE%" "%MAIN_PY%"
) else (
    echo pythonw.exe 不存在，使用 python.exe 启动（会显示控制台窗口）
    start "" "%PYTHON_EXE%" "%MAIN_PY%"
)

echo 应用已启动，此窗口可以关闭。
timeout /t 3 /nobreak >nul
