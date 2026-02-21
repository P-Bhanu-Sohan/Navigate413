#!/bin/bash
# Navigate413 Development Setup Script

set -e

echo "🚀 Navigate413 - Development Environment Setup"
echo "============================================="
echo ""

# Check Python version
echo "📦 Checking Python version..."
python3 --version || (echo "❌ Python 3 is required" && exit 1)

# Setup Backend
echo ""
echo "📦 Setting up backend..."
cd backend

# Create virtual environment
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Create .env if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file (please fill in your API keys)..."
    cp .env.example .env
    echo "⚠️  Please update backend/.env with your credentials:"
    echo "   - GEMINI_API_KEY: Your Google Gemini API key"
    echo "   - MONGODB_URI: Your MongoDB Atlas connection string"
fi

cd ..

# Setup Frontend
echo ""
echo "📦 Setting up frontend..."
cd frontend

# Check Node.js
command -v node &> /dev/null || (echo "❌ Node.js is required. Install from https://nodejs.org/" && exit 1)

# Install dependencies
echo "Installing Node.js dependencies..."
npm install

cd ..

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "1. Update backend/.env with your API credentials"
echo "2. Start backend: cd backend && source venv/bin/activate && uvicorn main:app --reload"
echo "3. Start frontend: cd frontend && npm run dev"
echo "4. Open http://localhost:5173 in your browser"
echo ""
echo "📚 Documentation:"
echo "  - README.md: Project overview and setup instructions"
echo "  - IMPLEMENTATION.md: Detailed implementation status"
echo "  - copilot.md: Original technical PRD"
