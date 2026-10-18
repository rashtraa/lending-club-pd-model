@echo off
setlocal
cd /d "%~dp0"
set REPO=https://github.com/rashtraa/lending-club-pd-model.git

echo ==========================================================
echo   Pushing credit-pd-engine to GitHub
echo   %REPO%
echo ==========================================================
echo.

where git >nul 2>&1
if errorlevel 1 goto :nogit

if exist ".git" goto :haverepo
echo [1/4] Creating local repository...
git init -b main
if errorlevel 1 goto :fail
goto :staged

:haverepo
echo [1/4] Local repository already exists - reusing it.

:staged
echo [2/4] Staging files...
git add -A
if errorlevel 1 goto :fail

echo.
echo        These files will be uploaded:
git diff --cached --name-only
echo.

echo [3/4] Committing...
git commit -m "Credit risk PD engine on Lending Club 2007-2018" -m "WOE logistic scorecard, XGBoost benchmark, PD-anchored rating scale, competing-risks lifetime PD, and loss quantification. Test AUC 0.7076 out-of-time on 2015 vs Lending Club sub_grade at 0.7100, using public borrower attributes only."
if errorlevel 1 echo        (nothing new to commit - continuing)

echo [4/4] Pushing to GitHub...
git remote remove origin >nul 2>&1
git remote add origin %REPO%
if errorlevel 1 goto :fail
git push -u origin main
if errorlevel 1 goto :pushfail

echo.
echo ==========================================================
echo   DONE
echo   https://github.com/rashtraa/lending-club-pd-model
echo ==========================================================
pause
exit /b 0

:nogit
echo ERROR: git is not installed, or not on your PATH.
echo Install it from https://git-scm.com/download/win and run this again.
pause
exit /b 1

:pushfail
echo.
echo PUSH FAILED. The two usual causes:
echo   1. The repo does not exist yet on GitHub. Create an EMPTY one named
echo      lending-club-pd-model at https://github.com/new
echo      (no README, no .gitignore, no licence - leave all boxes unticked)
echo   2. Sign-in was cancelled. Run this again and complete the GitHub prompt.
pause
exit /b 1

:fail
echo.
echo Something failed above. Copy the error text and send it to Claude.
pause
exit /b 1
