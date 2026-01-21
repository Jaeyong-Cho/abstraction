#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BACKEND_PORT=${1:-5000}
FRONTEND_PORT=${2:-5173}

echo "=========================================="
echo "Abstraction Level Tracker - Development Mode"
echo "=========================================="
echo ""

if [ ! -d ".abstraction" ]; then
    echo "Error: .abstraction directory not found"
    echo "Please run: python3 -m cli.main init ."
    exit 1
fi

cleanup() {
    echo ""
    echo "Shutting down servers..."
    kill $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    wait $BACKEND_PID $FRONTEND_PID 2>/dev/null || true
    echo "Servers stopped"
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "Starting backend server on http://localhost:$BACKEND_PORT"
python3 -m cli.main serve "$BACKEND_PORT" &
BACKEND_PID=$!

sleep 2

echo "Starting frontend dev server on http://localhost:$FRONTEND_PORT"
cd frontend
PORT=$FRONTEND_PORT npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "=========================================="
echo "Development servers running:"
echo "  Backend:  http://localhost:$BACKEND_PORT"
echo "  Frontend: http://localhost:$FRONTEND_PORT"
echo "=========================================="
echo "Press Ctrl+C to stop both servers"
echo ""

wait
