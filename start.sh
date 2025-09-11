#!/bin/bash

# DF-InfoUI Startup Script

echo "🚀 Starting DF-InfoUI..."

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  .env file not found. Creating from template..."
    cp server/env.example .env
    echo "📝 Please edit .env file and add your OpenAI API key"
    echo "   OPENAI_API_KEY=your_openai_api_key_here"
    exit 1
fi

# Check if OpenAI API key is set
if ! grep -q "OPENAI_API_KEY=sk-" .env; then
    echo "⚠️  OpenAI API key not configured in .env file"
    echo "   Please add your OpenAI API key to the .env file"
    exit 1
fi

# Create data directory
mkdir -p data

# Start services
echo "🐳 Starting Docker services..."
docker-compose up --build

echo "✅ DF-InfoUI is running!"
echo "   Frontend: http://localhost:3000"
echo "   Backend:  http://localhost:8000"
echo "   API Docs: http://localhost:8000/docs"
