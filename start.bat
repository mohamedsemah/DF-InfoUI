@echo off
REM DF-InfoUI Startup Script for Windows

echo 🚀 Starting DF-InfoUI...

REM Check if .env file exists
if not exist .env (
    echo ⚠️  .env file not found. Creating from template...
    copy server\env.example .env
    echo 📝 Please edit .env file and add your OpenAI API key
    echo    OPENAI_API_KEY=your_openai_api_key_here
    pause
    exit /b 1
)

REM Check if OpenAI API key is set
findstr /C:"OPENAI_API_KEY=sk-" .env >nul
if errorlevel 1 (
    echo ⚠️  OpenAI API key not configured in .env file
    echo    Please add your OpenAI API key to the .env file
    pause
    exit /b 1
)

REM Create data directory
if not exist data mkdir data

REM Start services
echo 🐳 Starting Docker services...
docker-compose up --build

echo ✅ DF-InfoUI is running!
echo    Frontend: http://localhost:3000
echo    Backend:  http://localhost:8000
echo    API Docs: http://localhost:8000/docs
