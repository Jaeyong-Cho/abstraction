#!/bin/bash

set -e

echo "=========================================="
echo "Abstraction Level Tracker - Setup"
echo "=========================================="
echo ""

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "[1/4] Checking Python installation..."
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is not installed"
    exit 1
fi

PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
echo "Found Python $PYTHON_VERSION"
echo ""

echo "[2/4] Installing Python dependencies..."
if [ -f "requirements.txt" ]; then
    python3 -m pip install --upgrade pip
    python3 -m pip install -r requirements.txt
    echo "Python dependencies installed successfully"
else
    echo "Warning: requirements.txt not found"
fi
echo ""

echo "[3/4] Checking Node.js installation..."
if ! command -v node &> /dev/null; then
    echo "Error: Node.js is not installed"
    echo "Please install Node.js from https://nodejs.org/"
    exit 1
fi

NODE_VERSION=$(node --version)
echo "Found Node.js $NODE_VERSION"
echo ""

echo "[4/4] Installing frontend dependencies..."
if [ -d "frontend" ]; then
    cd frontend
    if [ -f "package.json" ]; then
        npm install
        echo "Frontend dependencies installed successfully"
    else
        echo "Warning: frontend/package.json not found"
    fi
    cd ..
else
    echo "Warning: frontend directory not found"
fi
echo ""

echo "=========================================="
echo "Setup completed successfully!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "  1. Initialize project:  python3 -m cli.main init ."
echo "  2. Index your code:     python3 -m cli.main index <source_dir>"
echo "  3. Run the app:          ./run.sh"
echo "  4. Or run in dev mode:   ./run-dev.sh"
echo ""
