# 📘 Hướng Dẫn Lab #28 — Full Platform Integration Sprint

**Môn học:** AICB-P2T2 · Chương 6: Tổng Hợp  
**Thời gian:** 2 giờ  
**Mục tiêu:** Ghép toàn bộ stack kiến trúc AI platform hoàn chỉnh, end-to-end từ data ingestion → model serving → observability.

---

## 📋 1. Tổng Quan Project

> **Thư mục project hiện tại:** `Day28-Lab-Assignment/`  
> Tất cả source code, cấu hình Docker, scripts và tests đã được chuẩn bị sẵn.  

Xây dựng một **AI Platform** với kiến trúc **100% Local (GPU máy thật)** bao gồm:

| Thành phần | Công nghệ | Vai trò |
|-----------|-----------|---------|
| Message Broker | **Kafka** | Hàng đợi sự kiện, decouple components |
| Workflow Orchestrator | **Prefect** | Điều phối pipeline xử lý dữ liệu |
| Data Lake | **Delta Lake (Parquet)** | Lưu trữ dữ liệu thô dạng batch |
| Feature Store | **Feast (Redis)** | Lưu features cho serving |
| Vector Store | **Qdrant** | Lưu vector embeddings cho semantic search |
| API Gateway | **FastAPI** | Đầu mối xử lý request từ client |
| LLM Serving | **vLLM (Local GPU)** | Inference model Qwen2.5-0.5B-Instruct (siêu nhẹ) |
| Embedding Service | **Sentence-Transformers (Local GPU/CPU)** | Tạo vector embeddings (bge-small-en-v1.5) |
| Experiment Tracking | **MLflow** | Log metrics, parameters, model registry |
| Monitoring | **Prometheus + Grafana** | Metrics & visualization |
| Tracing | **LangSmith** | Trace LLM calls |

---

## 🏗️ 2. Kiến Trúc & Các Luồng Hoạt Động

### 2.1. Sơ Đồ Kiến Trúc Tổng Thể

```
┌──────────────────────────────────────────────────────────────┐
│                    LOCAL (Docker Compose)                      │
│                                                               │
│  ① Data Ingestion                                              │
│  scripts/01_ingest_to_kafka.py                                 │
│       │                                                        │
│       ▼                                                        │
│  Kafka ────► ② Prefect Pipeline                                │
│  (data.raw)     prefect/flows/kafka_to_delta.py                │
│                    │                                            │
│                    ▼                                            │
│               Delta Lake (Parquet)                             │
│                    │                                            │
│         ┌─────────┴──────────┐                                 │
│         ▼                     ▼                                 │
│  ③ Feast (Redis)       ⑤ Embedding → Qdrant                  │
│  (Feature Store)        (Vector Store)                         │
│                                   │                             │
│                                   ▼                             │
│  ⑧ API Gateway (FastAPI :8000) ◄─────────────────────────┐    │
│      │                       │                           │    │
│      │         ┌─────────────┘                           │    │
│      ▼         ▼                                         │    │
│  ⑨ Prometheus   ⑩ LangSmith                              │    │
│      │                                                    │    │
│      ▼                                                    │    │
│  Grafana (:3000)                                          │    │
│                                                           │    │
└───────────────────────────────────────────────────────────┼────┘
                                                            │
                                        
┌───────────────────────────────────────────────────────────┐
│              LOCAL GPU (máy thật)                          │
│                                                           │
│  ⑥ MLflow ──► Model Registry                              │
│                                                           │
│  ⑦ vLLM Serving (:8001) ────► API Gateway calls LLM      │
│  ⑤ Embedding Service (:8002) ──► Tạo vectors cho Qdrant   │
└───────────────────────────────────────────────────────────┘
```

### 2.2. 10 Integration Points Cần Kết Nối

| # | Integration | Mô Tả | Script/File |
|---|------------|-------|-------------|
| 1 | **Data → Kafka** | Gửi dữ liệu mẫu vào Kafka topic `data.raw` | `scripts/01_ingest_to_kafka.py` |
| 2 | **Kafka → Prefect** | Prefect flow consume từ Kafka, xử lý và lưu vào Delta Lake | `prefect/flows/kafka_to_delta.py` |
| 3 | **Delta Lake → Feast** | Đọc Parquet từ Delta Lake, push features lên Redis (Feast online store) | `scripts/03_delta_to_feast.py` |
| 4 | **Feast → API Gateway** | API Gateway đọc features từ Redis để enrich context | (tích hợp trong `api-gateway/main.py`) |
| 5 | **Data → Embedding → Qdrant** | Gọi local embedding service (port 8002), lưu vectors vào Qdrant | `scripts/05_embed_to_qdrant.py` |
| 6 | **MLflow → Model Registry** | Log model params, metrics, và serving URL lên MLflow | (chạy local) |
| 7 | **vLLM Serving** | Serve model Qwen2.5-0.5B-Instruct qua API OpenAI-compatible trên local GPU | `scripts/run_llm.py` |
| 8 | **API Gateway → vLLM** | API Gateway gọi LLM trực tiếp qua HTTP (localhost:8001) | `api-gateway/main.py` |
| 9 | **Prometheus Metrics** | API Gateway expose metrics → Prometheus scrape → Grafana dashboard | `monitoring/prometheus.yml` |
| 10 | **LangSmith Tracing** | Trace các LLM calls và gửi lên LangSmith | `api-gateway/main.py` |

### 2.3. Luồng Dữ Liệu Chi Tiết

```
[User] ──HTTP──► API Gateway (:8000)
                  │
                  ├─► Qdrant: tìm kiếm vector tương đồng (context)
                  │
                  ├─► Redis: lấy features từ Feast
                  │
                  └─► vLLM (Local :8001): gửi prompt + context → nhận answer
                  │
                  └─► Prometheus: ghi metrics (latency, request count)
                  │
                  └─► LangSmith: trace LLM call
                  │
                  ◄── Trả về response cho user
```

---

## ✅ 3. Todo List — Các Việc Cần Làm

> **Lưu ý:** Project đã được setup sẵn đầy đủ file cấu trúc trong thư mục `Day28-Lab-Assignment/`. Các bước Phase 1 (tạo file) đã hoàn thành. Bây giờ cần chạy các services và scripts.

### Phase 1: Infrastructure Setup ✅ (Đã hoàn thành)
- [x] **1.1** Thư mục project structure (`Day28-Lab-Assignment/`)
- [x] **1.2** `docker-compose.yml` (Kafka, Prefect, Qdrant, Redis, Prometheus, Grafana, API Gateway)
- [x] **1.3** `monitoring/prometheus.yml` cấu hình scrape targets
- [x] **1.4** `api-gateway/Dockerfile` và `api-gateway/main.py`
- [x] **1.5** `api-gateway/requirements.txt`
- [x] **1.6** `prefect/flows/kafka_to_delta.py` (Prefect flow)
- [x] **1.7** `prefect/flows/requirements.txt`
- [ ] **1.8** Khởi động Docker Compose: `docker compose up -d`

### Phase 2: Local GPU Setup
- [ ] **2.1** Cài dependencies: `pip install vllm fastapi uvicorn sentence-transformers httpx`
- [ ] **2.2** Chạy embedding service: `python scripts/run_embedding.py` (port 8002)
- [ ] **2.3** Chạy vLLM server: `python scripts/run_llm.py` (port 8001, model Qwen2.5-0.5B-Instruct)
- [ ] **2.4** Hoặc chạy cùng lúc: `bash scripts/run_local_services.sh`
- [ ] **2.5** Log model info lên MLflow

### Phase 3: Data Pipeline
- [ ] **3.1** Chạy `scripts/01_ingest_to_kafka.py` — gửi dữ liệu vào Kafka
- [ ] **3.2** Deploy Prefect flow: chạy `kafka_to_delta.py`
- [ ] **3.3** Chạy Prefect worker: `prefect worker start -p docker -n lab28-worker`
- [ ] **3.4** Chạy `scripts/03_delta_to_feast.py` — push features lên Redis
- [ ] **3.5** Chạy `scripts/05_embed_to_qdrant.py` — tạo embeddings và lưu vào Qdrant

### Phase 4: API & Observability
- [ ] **4.1** Kiểm tra API Gateway: `curl http://localhost:8000/health`
- [ ] **4.2** Test chat endpoint: `POST /api/v1/chat`
- [ ] **4.3** Kiểm tra Prometheus: `http://localhost:9090`
- [ ] **4.4** Kiểm tra Grafana: `http://localhost:3000` (admin/admin)
- [ ] **4.5** Chạy script verify observability: `scripts/09_verify_observability.py`

### Phase 5: Validation & Submission
- [ ] **5.1** Chạy smoke tests: `pytest smoke-tests/ -v` (kỳ vọng 5/5 pass)
- [ ] **5.2** Chạy production readiness check: `python scripts/production_readiness_check.py`
- [ ] **5.3** Chụp screenshots (Prefect UI, API Gateway, Grafana)
- [ ] **5.4** Push code lên GitHub repo
- [ ] **5.5** Trả lời 5 câu hỏi nộp bài

---

## 🔧 4. Hướng Dẫn Setup

### 4.1. Yêu Cầu Hệ Thống

| Công cụ | Yêu cầu | Kiểm tra |
|---------|---------|----------|
| Docker Desktop | Đang chạy | `docker ps` |
| Python | >= 3.10 | `python --version` |
| pip | Latest | `pip --version` |
| NVIDIA GPU (hoặc CPU) | GPU drivers installed | `nvidia-smi` |

### 4.2. Cài Đặt Công Cụ

```bash
# Cài vLLM + các dependencies cần thiết
pip install vllm fastapi uvicorn sentence-transformers httpx
```

### 4.3. Khởi Động Local Stack

```bash
# Vào thư mục project (đã có sẵn tất cả files)
cd Day28-Lab-Assignment

# File .env đã được cấu hình sẵn (local services)
# VLLM_URL=http://host.docker.internal:8001
# EMBED_URL=http://host.docker.internal:8002
# LLM_MODEL=Qwen/Qwen2.5-0.5B-Instruct

# Khởi động tất cả services
docker compose up -d

# Kiểm tra
docker compose ps
# Kỳ vọng: Tất cả services (7 containers) đều "Up"
```

### 4.4. Kiểm Tra Services

| Service | URL | Credentials |
|---------|-----|-------------|
| Prefect UI | http://localhost:4200 | - |
| Grafana | http://localhost:3000 | admin / admin |
| Qdrant Dashboard | http://localhost:6333/dashboard | - |
| Prometheus | http://localhost:9090 | - |
| API Gateway | http://localhost:8000 | - |

### 4.5. Setup Kaggle Notebook

1. Vào [kaggle.com](https://kaggle.com) → Create Notebook
2. Settings → Accelerator → **GPU T4 x2**
3. Chạy local GPU services: `bash scripts/run_local_services.sh` (xem hướng dẫn trong `LAB28_GUIDE.md` Phần 2)
4. File `.env` đã được cấu hình sẵn với local URLs

### 4.6. Chạy Các Script Theo Thứ Tự

> **Lưu ý:** Tất cả commands chạy từ thư mục gốc `Day28-Lab-Assignment/`.

```bash
# Bước 1: Ingest dữ liệu vào Kafka
python scripts/01_ingest_to_kafka.py

# Bước 2: Deploy Prefect flow (chạy trong terminal riêng)
cd prefect/flows
pip install -r requirements.txt
python kafka_to_delta.py
# Sau đó start worker:
prefect worker start -p docker -n lab28-worker

# Bước 3: Push features lên Feast (Redis)
python scripts/03_delta_to_feast.py

# Bước 4: Embed và lưu vào Qdrant
python scripts/05_embed_to_qdrant.py

# Bước 5: Kiểm tra observability
export LANGCHAIN_API_KEY=<your_key>
python scripts/09_verify_observability.py

# Bước 6: Production readiness check
python scripts/production_readiness_check.py

# Bước 7: Smoke tests
pytest smoke-tests/ -v
```

---

## 🎯 5. Tiêu Chí Chấm Điểm & Điều Kiện Pass

### 5.1. Thang Điểm

| Tiêu Chí | Trọng Số | Mô Tả | Pass Nếu |
|----------|----------|-------|-----------|
| **Integration Completeness** | 40% | 10 integration points hoạt động, data flow end-to-end | ≥ 8/10 integrations hoạt động |
| **Observability** | 25% | Logs, metrics, traces hiển thị; alerts configured | Prometheus scrape được, Grafana hiển thị metrics, LangSmith có traces |
| **Performance** | 20% | Latency trong SLO; load tested; không memory leaks | API latency < 2000ms, health check luôn 200 |
| **Architecture Quality** | 15% | Clean separation, GitOps config, documented decisions | Code có cấu trúc, có README, có error handling |

### 5.2. Điều Kiện Đậu (Pass)

✅ **BẮT BUỘC** — Tất cả điều kiện sau phải đạt:

| # | Điều Kiện | Cách Kiểm Tra |
|---|-----------|---------------|
| 1 | **Smoke tests pass 5/5** | `pytest smoke-tests/ -v` — tất cả tests xanh |
| 2 | **Production Readiness Score > 80%** | `python scripts/production_readiness_check.py` — score > 80% |
| 3 | **API Gateway health OK** | `curl http://localhost:8000/health` → `{"status": "ok"}` |
| 4 | **Prefect flow deployed & chạy được** | Prefect UI: http://localhost:4200 thấy flow |
| 5 | **Grafana dashboard accessible** | http://localhost:3000 → login admin/admin |
| 6 | **Qdrant có documents** | http://localhost:6333/collections/documents → points_count > 0 |
| 7 | **Feast (Redis) có features** | Redis có keys `feature:*` |

### 5.3. Các Artifacts Cần Nộp

```
lab28_submission_[student_id]/
├── Day28-Lab-Assignment/           # Source code hoàn chỉnh (thư mục gốc)
│   ├── docker-compose.yml
│   ├── .env (ẩn, chứa URLs local GPU)
│   ├── prefect/flows/
│   │   ├── kafka_to_delta.py
│   │   └── requirements.txt
│   ├── scripts/
│   │   ├── 01_ingest_to_kafka.py
│   │   ├── 03_delta_to_feast.py
│   │   ├── 05_embed_to_qdrant.py
│   │   ├── 09_verify_observability.py
│   │   ├── production_readiness_check.py
│   │   ├── run_llm.py (chạy vLLM local)
│   │   ├── run_embedding.py (chạy embedding local)
│   │   └── run_local_services.sh (chạy tất cả local GPU services)
│   ├── api-gateway/
│   │   ├── Dockerfile
│   │   ├── main.py
│   │   └── requirements.txt
│   ├── monitoring/
│   │   └── prometheus.yml
│   ├── smoke-tests/
│   │   └── test_e2e.py
│   ├── LAB28_GUIDE.md
│   ├── SUBMISSION.md
│   └── README.md
├── screenshots/
│   ├── prefect_ui.png              # Prefect UI có flow đang chạy
│   ├── api_gateway.png             # curl response hoặc Swagger UI
│   └── grafana_dashboard.png       # Grafana dashboard hiển thị metrics
├── smoke_tests_results.png         # Kết quả pytest (5/5 pass)
├── production_readiness.png        # Score > 80%
└── README.md                       # Hướng dẫn setup
```

### 5.4. 5 Câu Hỏi Cần Trả Lời Khi Nộp

1. **Phân tích các trade-offs trong thiết kế kiến trúc AI platform của bạn. Bạn đã cân bằng giữa performance, reliability, và maintainability như thế nào?**

2. **Trong kiến trúc hybrid (Local + Kaggle), bạn xử lý ngắt kết nối giữa local và Kaggle như thế nào? Có cơ chế fallback không?**

3. **Giải thích cách event-driven architecture với Kafka giúp decouple các components trong AI platform của bạn.**

4. **Bạn đã implement observability như thế nào? Logs, metrics, và traces được thu thập và visualized ra sao?**

5. **Nếu một service trong stack (ví dụ: Qdrant hoặc Kafka) bị crash, hệ thống của bạn sẽ xử lý như thế nào? Có graceful degradation không?**

---

## ⚠️ 6. Các Vấn Đề Cần Tránh

| Vấn đề | Giải Pháp |
|--------|-----------|
| Config drift giữa các environments | Dùng `.env` file, không hardcode URLs |
| Thiếu error handling tại integration points | Try-except, graceful degradation, retry logic |
| Monitoring coverage không hoàn chỉnh | Đảm bảo Prometheus scrape được API Gateway, Kafka, Prefect |
| Không có rollback strategy | Git version control, Docker tags |
| Demo không test trước khi nộp | Chạy smoke tests trước khi chụp screenshot |
| Local GPU services chưa chạy | Kiểm tra `curl http://localhost:8001/health` và `curl http://localhost:8002/health` |
| Kaggle session bị timeout | Keep Kaggle tab active, reconnect tunnels nếu cần |

---

## 🚀 7. Tóm Tắt Nhanh Các Lệnh Quan Trọng

```bash
# Di chuyển vào thư mục project
cd Day28-Lab-Assignment

# Docker
docker compose up -d                          # Start all services
docker compose ps                             # Kiểm tra services
docker compose logs -f api-gateway            # Xem logs API Gateway
docker compose down                           # Dừng tất cả

# Tests
pytest smoke-tests/ -v                        # Chạy smoke tests
python scripts/production_readiness_check.py   # Kiểm tra production readiness

# API
curl http://localhost:8000/health              # Health check
curl -X POST http://localhost:8000/api/v1/chat \
  -H "Content-Type: application/json" \
  -d '{"query":"Hello","embedding":[0.1]*384}' # Chat

# Kafka
docker exec lab28-kafka-1 kafka-topics --list --bootstrap-server localhost:9092

# Redis
redis-cli keys 'feature:*'                     # Kiểm tra features

# Prefect
prefect worker start -p docker -n lab28-worker # Start worker
```

---

## 📚 Tài Liệu Tham Khảo

- [Prefect Docs](https://docs.prefect.io/)
- [vLLM Docs](https://docs.vllm.ai/)
- [Qdrant Docs](https://qdrant.tech/documentation/)
- [Prometheus Docs](https://prometheus.io/docs/)
- [Grafana Docs](https://grafana.com/docs/)
- [LangSmith Docs](https://docs.smith.langchain.com/)
- [Feast Docs](https://docs.feast.dev/)
- [vLLM Docs](https://docs.vllm.ai)
- [Cloudflared Docs](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/)
