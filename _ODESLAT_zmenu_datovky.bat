@echo off
REM Jednoducha pomucka: odesle upravenou obrazovku datovek na GitHub.
REM Staci dvojklik. Okno se na konci samo nezavre, abys videla vysledek.
cd /d C:\Projekty\Strategie

echo ============================================================
echo  Odesilam zmenu (apps\api\static\mobile.html) na GitHub...
echo ============================================================
echo.

git add apps/api/static/mobile.html
git commit -m "mobile: vyrazny banner u synchronizace datovek"
git push origin main
set RES=%errorlevel%

echo.
if "%RES%"=="0" (
  echo ------------------------------------------------------------
  echo  HOTOVO. Zmena je odeslana na GitHub.
  echo  Ted muzes pokracovat NASAZENIM na server.
  echo ------------------------------------------------------------
) else (
  echo ------------------------------------------------------------
  echo  NECO SE NEPOVEDLO. Vyfot/oskenuj tohle okno a posli to Claudovi.
  echo ------------------------------------------------------------
)
echo.
pause
