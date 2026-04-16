@echo off
setlocal ENABLEDELAYEDEXPANSION
chcp 65001 >nul

REM Fast, non-interactive pip
set PIP_NO_INPUT=1
set PIP_PROGRESS_BAR=off

REM Ensure pip exists in venv
if not exist "sign_lang_env\Scripts\python.exe" (
  echo [ERROR] Virtual environment not found at sign_lang_env\Scripts\python.exe
  echo Create or fix the venv, then rerun this script.
  exit /b 1
)

"sign_lang_env\Scripts\python.exe" -m ensurepip --default-pip

REM Upgrade tooling
"sign_lang_env\Scripts\python.exe" -m pip install --upgrade pip setuptools wheel --disable-pip-version-check --no-color

REM Chunk 1: core scientific/runtime
"sign_lang_env\Scripts\python.exe" -m pip install ^
  numpy==1.23.5 requests Pillow==11.3.0 joblib==1.5.2 scikit-image==0.24.0 ^
  --no-color --disable-pip-version-check
if errorlevel 1 goto :install_error

REM Chunk 2: Flask stack
"sign_lang_env\Scripts\python.exe" -m pip install ^
  Flask==3.1.2 Flask-Session==0.8.0 Flask-SocketIO==5.5.1 ^
  --no-color --disable-pip-version-check
if errorlevel 1 goto :install_error

REM Chunk 3: CV and helpers
"sign_lang_env\Scripts\python.exe" -m pip install ^
  opencv-python==4.11.0.86 mediapipe==0.10.21 arabic-reshaper==3.0.0 python-bidi==0.6.6 pyspellchecker==0.8.3 ^
  --no-color --disable-pip-version-check
if errorlevel 1 goto :install_error

REM Chunk 4: Firebase
"sign_lang_env\Scripts\python.exe" -m pip install ^
  firebase-admin==7.1.0 ^
  --no-color --disable-pip-version-check
if errorlevel 1 goto :install_error

REM Chunk 5: TensorFlow (this may take several minutes)
"sign_lang_env\Scripts\python.exe" -m pip install ^
  tensorflow==2.12.0 tensorflow-intel==2.12.0 keras==2.12.0 tensorboard==2.12.3 tensorflow-io-gcs-filesystem==0.31.0 ^
  protobuf==4.25.8 grpcio==1.75.0 typing_extensions==4.15.0 wrapt==1.14.2 h5py==3.14.0 absl-py==2.3.1 opt-einsum==3.4.0 six==1.17.0 ^
  --no-color --disable-pip-version-check
if errorlevel 1 goto :install_error

echo.
echo ============================================
echo Dependencies installed successfully.
echo Starting server on http://localhost:5001
echo ============================================
echo.

REM Launch the app on localhost:5001
"sign_lang_env\Scripts\python.exe" app.py --host localhost --port 5001
exit /b %errorlevel%

:install_error
echo.
echo [ERROR] A dependency installation step failed. Please do not close the window.
echo If this was accidental (Ctrl+C), run this script again without interruption.
exit /b 1
