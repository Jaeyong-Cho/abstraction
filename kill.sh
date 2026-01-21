#!/bin/bash

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

BACKEND_PORT=${1:-5000}
FRONTEND_PORT=${2:-5173}

echo "=========================================="
echo "Abstraction Level Tracker - Stop Servers"
echo "=========================================="
echo ""

KILLED=0

echo "Stopping backend server (port $BACKEND_PORT)..."
BACKEND_PIDS=$(lsof -ti:$BACKEND_PORT 2>/dev/null || true)
if [ -n "$BACKEND_PIDS" ]; then
    echo "$BACKEND_PIDS" | xargs kill -9 2>/dev/null || true
    echo "Backend server stopped"
    KILLED=1
else
    echo "No backend server found on port $BACKEND_PORT"
fi
echo ""

echo "Stopping frontend dev server (port $FRONTEND_PORT)..."
FRONTEND_PIDS=$(lsof -ti:$FRONTEND_PORT 2>/dev/null || true)
if [ -n "$FRONTEND_PIDS" ]; then
    echo "$FRONTEND_PIDS" | xargs kill -9 2>/dev/null || true
    echo "Frontend dev server stopped"
    KILLED=1
else
    echo "No frontend dev server found on port $FRONTEND_PORT"
fi
echo ""

if [ $KILLED -eq 0 ]; then
    echo "No servers were running"
else
    echo "All servers stopped successfully"
fi
echo ""
