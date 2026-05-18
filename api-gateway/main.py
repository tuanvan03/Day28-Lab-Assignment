# api-gateway/main.py
from fastapi import FastAPI, Request
from prometheus_fastapi_instrumentator import Instrumentator
import httpx, os, time

app = FastAPI(title="AI Platform API Gateway")
Instrumentator().instrument(app).expose(app)  # Integration 9: Prometheus

VLLM_URL = os.environ["VLLM_URL"]
EMBED_URL = os.environ.get("EMBED_URL", "http://localhost:8002")
QDRANT_URL = os.environ.get("QDRANT_URL", "http://qdrant:6333")
LLM_MODEL = os.environ.get("LLM_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")


@app.post("/api/v1/chat")
async def chat(request: Request):
    body = await request.json()
    query = body.get("query")
    if not query:
        from fastapi import HTTPException
        raise HTTPException(status_code=422, detail="Field 'query' is required")
    start = time.time()

    async with httpx.AsyncClient() as client:
        # 1. Generate embedding locally
        embed_resp = await client.post(f"{EMBED_URL}/embed", json={"texts": [query]})
        embedding = embed_resp.json()["embeddings"][0]

        # 2. Vector search in Qdrant
        search_resp = await client.post(f"{QDRANT_URL}/collections/documents/points/search", json={
            "vector": embedding,
            "limit": 3
        })
        context = search_resp.json().get("result", [])

    # 3. LLM inference
    prompt = f"Context: {context}\n\nQuery: {query}"
    async with httpx.AsyncClient(timeout=30) as client:
        llm_resp = await client.post(f"{VLLM_URL}/v1/chat/completions", json={
            "model": LLM_MODEL,
            "messages": [{"role": "user", "content": prompt}]
        })

    latency = (time.time() - start) * 1000
    result = llm_resp.json()

    return {
        "answer": result["choices"][0]["message"]["content"],
        "latency_ms": round(latency, 2),
        "model": result["model"]
    }


@app.get("/health")
def health():
    return {"status": "ok"}
