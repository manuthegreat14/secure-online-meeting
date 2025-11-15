@echo off
echo Starting Online Interview Platform...
echo.
echo Make sure Redis is running before starting the application
echo.
python manage.py runserver 0.0.0.0:8000
pause



