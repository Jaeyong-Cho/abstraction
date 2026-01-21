#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

PORT=${1:-5000}

echo "=========================================="
echo "Abstraction Level Tracker - Production Mode"
echo "=========================================="
echo ""

if [ ! -d ".abstraction" ]; then
    echo "Error: .abstraction directory not found"
    echo "Please run: python3 -m cli.main init ."
    exit 1
fi

if [ ! -d "frontend/dist" ]; then
    echo "Frontend not built. Building now..."
    cd frontend
    npm run build
    cd ..
    echo ""
fi

echo "Starting server on http://localhost:$PORT"
echo "Press Ctrl+C to stop"
echo ""

python3 -m cli.main serve "$PORT"
