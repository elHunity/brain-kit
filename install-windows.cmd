@echo off
rem Second Brain installer for Windows 10/11.
rem Installs programs from their makers via winget (Microsoft), asks before each one,
rem copies the second brain folder to Documents\SecondBrain and opens it.
rem Test mode: set SECONDBRAIN_TEST=1, SECONDBRAIN_DIR, SECONDBRAIN_VENV, OBSIDIAN_CONFIG - nothing is installed or opened.
setlocal EnableExtensions EnableDelayedExpansion
rem no "chcp 65001": with it, set /p reads nothing from redirected input (found in tests). All text here is ASCII.
title Second Brain setup
set "KIT=%~dp0"
set "BRAIN=%USERPROFILE%\Documents\SecondBrain"
set "VENV=%USERPROFILE%\.secondbrain-venv"
if defined SECONDBRAIN_DIR set "BRAIN=%SECONDBRAIN_DIR%"
if defined SECONDBRAIN_VENV set "VENV=%SECONDBRAIN_VENV%"

echo.
echo  ==============================================
echo    Second Brain - setup
echo  ==============================================
echo.
echo  This will install a few free programs from their official makers
echo  and set up your second brain. It asks before each step.
echo  Nothing about you is sent to the person who gave you this.
echo.
if not defined SECONDBRAIN_TEST pause

where winget >nul 2>&1
if errorlevel 1 (
  echo.
  echo  winget, the Windows installer, is missing. Update "App Installer" in Microsoft Store and run this again.
  pause
  exit /b 1
)

echo.
echo  --- Step 1 of 4: programs ---
call :app Git.Git "Git - lets the assistant save restore points of your notes"
call :app Microsoft.VisualStudioCode "VS Code - the window where you talk to Claude"
call :app Python.Python.3.12 "Python - needed for the voice"
call :app Obsidian.Obsidian "Obsidian - shows your notes nicely, free"
call :app WisprFlow.WisprFlow "Wispr Flow - voice typing, free 2,000 words a week"

echo.
echo  --- Step 2 of 4: your second brain folder ---
if exist "%BRAIN%\AGENTS.md" (
  echo  Found an existing second brain in %BRAIN% - keeping your notes, not touching it.
  goto voice
)
robocopy "%KIT%vault" "%BRAIN%" /E /NFL /NDL /NJH /NJS /NP >nul
if errorlevel 8 (
  echo  Could not copy the folder to %BRAIN%.
  pause
  exit /b 1
)
echo  Created %BRAIN%
echo.
echo  Which language should it speak with you?
echo    1 - English    2 - Russian    3 - Hebrew    4 - other
set "LANGNUM="
set /p "LANGNUM=  Type a number and press Enter: "
set "ULANG=English"
if "%LANGNUM%"=="2" set "ULANG=Russian"
if "%LANGNUM%"=="3" set "ULANG=Hebrew"
if "%LANGNUM%"=="4" set /p "ULANG=  Type your language in English: "
>>"%BRAIN%\00-Profile.md" echo Language: !ULANG!
call :findgit
if defined GIT (
  "%GIT%" -C "%BRAIN%" init -q
  "%GIT%" -C "%BRAIN%" config user.name "Second Brain"
  "%GIT%" -C "%BRAIN%" config user.email "second-brain@localhost"
  "%GIT%" -C "%BRAIN%" config core.autocrlf false
  "%GIT%" -C "%BRAIN%" add -A 2>nul
  "%GIT%" -C "%BRAIN%" commit -q -m "Start"
  echo  Restore points: on.
) else (
  echo  Git not found - restore points are off. Install Git and run this again to turn them on.
)

:voice
echo.
echo  --- Step 3 of 4: the voice ---
if exist "%VENV%\Scripts\python.exe" (
  echo  Voice: already set up.
  goto apps
)
call :findpython
if not defined PY (
  echo  Python not found - the assistant will answer in text only. Install Python and run this again for the voice.
  goto apps
)
"%PY%" -m venv "%VENV%"
"%VENV%\Scripts\python.exe" -m pip install --quiet --disable-pip-version-check edge-tts
if errorlevel 1 (
  echo  The voice could not be installed - check the internet and run this again.
) else (
  echo  Voice: ready. Say "voice off" to the assistant to turn it off.
)

:apps
echo.
echo  --- Step 4 of 4: opening ---
call :findcode
if defined SECONDBRAIN_TEST (
  echo  [test] would install the Claude extension and open VS Code and Obsidian
  set "PY=%VENV%\Scripts\python.exe"
  if exist "!PY!" "!PY!" "%KIT%setup\obsidian_register.py" "%BRAIN%"
  goto done
)
if defined CODE (
  call "%CODE%" --install-extension anthropic.claude-code --force
) else (
  echo  VS Code not found - install it, then add the "Claude Code" extension from its Extensions panel.
)
if exist "%VENV%\Scripts\python.exe" "%VENV%\Scripts\python.exe" "%KIT%setup\obsidian_register.py" "%BRAIN%"
start "" "obsidian://open?vault=SecondBrain"
if defined CODE call "%CODE%" "%BRAIN%"

:done
echo.
echo  ==============================================
echo    Done. What's next:
echo    1. In VS Code, open Claude - the Claude icon on the left.
echo    2. Sign in with your Claude account - Pro or higher.
echo    3. Say or type "hi".
echo    To speak instead of typing: Wispr Flow, or press Win + H.
echo    Read "Welcome" in Obsidian for the rest.
echo  ==============================================
echo.
pause
exit /b 0

rem ---------- helpers ----------

:app
rem %1 = winget id, %2 = what it is
winget list --id %1 -e --accept-source-agreements <nul >nul 2>&1
if not errorlevel 1 (
  echo  %~2: already installed.
  exit /b 0
)
if defined SECONDBRAIN_TEST (
  echo  [test] would offer: %~2
  exit /b 0
)
set "ANS="
set /p "ANS=  Install %~2? [Y/N] "
if /i not "!ANS!"=="Y" (
  echo  Skipped.
  exit /b 0
)
winget install --id %1 -e --silent --accept-package-agreements --accept-source-agreements <nul
exit /b 0

:findgit
set "GIT="
for %%G in ("%ProgramFiles%\Git\cmd\git.exe" "%LOCALAPPDATA%\Programs\Git\cmd\git.exe") do if not defined GIT if exist %%G set "GIT=%%~G"
if not defined GIT for /f "delims=" %%G in ('where git 2^>nul') do if not defined GIT set "GIT=%%G"
exit /b 0

:findpython
set "PY="
for %%P in ("%LOCALAPPDATA%\Programs\Python\Python312\python.exe" "%ProgramFiles%\Python312\python.exe") do if not defined PY if exist %%P set "PY=%%~P"
if not defined PY for /f "delims=" %%P in ('where python 2^>nul ^| findstr /v /i "WindowsApps"') do if not defined PY set "PY=%%P"
exit /b 0

:findcode
set "CODE="
for %%C in ("%LOCALAPPDATA%\Programs\Microsoft VS Code\bin\code.cmd" "%ProgramFiles%\Microsoft VS Code\bin\code.cmd") do if not defined CODE if exist %%C set "CODE=%%~C"
exit /b 0
