@echo off
setlocal
if not exist index.html (
  echo Run this file from the root of your simba-cement2 repository.
  pause
  exit /b 1
)

python apply_production_fixes.py
if errorlevel 1 (
  echo.
  echo Fix script reported an error. Review the output above.
  pause
  exit /b 1
)

echo.
git diff --check
if errorlevel 1 (
  echo git diff --check found a problem.
  pause
  exit /b 1
)

echo.
echo Fixes applied. Review the changes with:
echo git diff
echo.
echo Then publish with:
echo git add -A
echo git commit -m "fix production readiness issues"
echo git push origin main
pause
