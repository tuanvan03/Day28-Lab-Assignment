#!/bin/bash
# ============================================================
# Start all local GPU services (replaces Kaggle setup)
# ============================================================
set -e

echo "╔══════════════════════════════════════════════════════════╗"
echo "║     Starting Local GPU AI Services                       ║"
echo "║     LLM: Qwen/Qwen2.5-0.5B-Instruct (port 8001)         ║"
echo "║     Embedding: BAAI/bge-small-en-v1.5 (port 8002)       ║"
echo "╚══════════════════════════════════════════════════════════╝"

# ── Check GPU ─────────────────────────────────────────────────
echo ""
echo "🔍 Checking GPU..."
if command -v nvidia-smi &> /dev/null; then
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
else
    echo "⚠️  No NVIDIA GPU detected. The models will run on CPU (slower)."
fi

# ── Kill any existing services on these ports ─────────────────
for port in 8001 8002; do
    pid=$(lsof -ti :$port 2>/dev/null || true)
    if [ -n "$pid" ]; then
        echo "🔴 Killing existing process on port $port (PID: $pid)"
        kill -9 $pid 2>/dev/null || true
    fi
done

# ── Start embedding service (background) ──────────────────────
echo ""
echo "📡 Starting embedding service (port 8002)..."
python scripts/run_embedding.py &
EMBED_PID=$!
echo "   PID: $EMBED_PID"

# Wait for embedding service to be ready
echo "⏳ Waiting for embedding service..."
for i in $(seq 1 30); do
    if curl -s http://localhost:8002/health > /dev/null 2>&1; then
        echo "✅ Embedding service ready!"
        break
    fi
    sleep 2
done

# ── Start vLLM server (foreground) ────────────────────────────
echo ""
echo "🤖 Starting vLLM server (port 8001)..."
echo "   Model: Qwen/Qwen2.5-0.5B-Instruct"
echo ""
echo "⚠️  This will take a minute to download and load the model."
echo "   Press Ctrl+C to stop both services."
echo ""

# Trap Ctrl+C to clean up background processes
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $EMBED_PID 2>/dev/null || true
    wait $EMBED_PID 2>/dev/null || true
    echo "✅ All services stopped."
    exit 0
}
trap cleanup SIGINT SIGTERM

python scripts/run_llm.py

# If vLLM exits, also stop embedding
cleanup
