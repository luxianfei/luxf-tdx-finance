@echo off
title Stop Stock Finance API Server

echo ================================================
echo    Stock Finance API Service - Stop Script
echo ================================================
echo.

taskkill /f /im python.exe /fi "windowtitle eq Stock Finance API Server"

echo.
echo Service stopped.
pause