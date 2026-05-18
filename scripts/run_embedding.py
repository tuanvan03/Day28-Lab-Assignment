#!/usr/bin/env python3
"""
Run embedding service locally using sentence-transformers.
Model: BAAI/bge-small-en-v1.5 (384-dim, lightweight, ~33MB).
"""
from fastapi import FastAPI, Request
from sentence_transformers import SentenceTransformer
import uvicorn
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="Local Embedding Service")
model = SentenceTransformer("BAAI/bge-small-en-v1.5", device="cpu")

@app.post("/embed")
async def embed(data: dict):
    texts = data["texts"]
    logger.info(f"Embedding {len(texts)} texts")
    embeddings = model.encode(texts).tolist()
    return {"embeddings": embeddings}

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    port = 8002
    print(f"🚀 Starting embedding service on port {port}...")
    print(f"   Model: BAAI/bge-small-en-v1.5 (384-dim)")
    uvicorn.run(app, host="0.0.0.0", port=port)
