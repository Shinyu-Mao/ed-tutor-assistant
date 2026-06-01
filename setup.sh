#!/bin/bash
# Quick setup for the Ed Tutor Assistant backend

set -e
cd "$(dirname "$0")/backend"

echo "Installing Python dependencies..."
pip install -r requirements.txt

if [ ! -f .env ]; then
  cp .env.example .env
  echo ""
  echo "  *** Created backend/.env — please add your ANTHROPIC_API_KEY ***"
  echo ""
fi

echo ""
echo "Setup complete. Start the backend with:"
echo "  cd backend && uvicorn server:app --reload --port 8765"
echo ""
echo "Then load the extension in Chrome:"
echo "  1. Go to chrome://extensions"
echo "  2. Enable 'Developer mode'"
echo "  3. Click 'Load unpacked' → select the 'extension/' folder"
