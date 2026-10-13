@echo off
rem Runs Python with GDAL from a QGIS installation (no separate GDAL install needed).
rem   run.bat -m firetower --dem DEM.tif --out results
rem   run.bat -m unittest discover -s tests -v
setlocal
set "QGIS_ENV="
for /d %%D in ("%ProgramFiles%\QGIS*") do if exist "%%D\bin\o4w_env.bat" set "QGIS_ENV=%%D\bin\o4w_env.bat"
if not defined QGIS_ENV (
  echo QGIS not found under "%ProgramFiles%". Install QGIS, or run with any Python that has GDAL 3.1+.
  exit /b 1
)
call "%QGIS_ENV%"
cd /d "%~dp0"
python %*
