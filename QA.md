1. Phân tích các trade-offs trong thiết kế kiến trúc AI platform của bạn. Bạn đã cân bằng giữa performance, reliability, và maintainability như thế nào?

Trả lời: Ưu tiên reliability và giới hạn tài nguyên — giảm VRAM cho vLLM, chạy embeddings trên CPU; dùng Docker + Prefect để dễ vận hành và duy trì.

2. Trong kiến trúc hybrid (Local + Kaggle), bạn xử lý ngắt kết nối giữa local và Kaggle như thế nào? Có cơ chế fallback không?

Trả lời: Có. Dùng biến môi trường và cấu hình để đổi endpoint; khi mất kết nối hoặc thiếu GPU, fallback sang CPU hoặc remote inference endpoint.

3. Giải thích cách event-driven architecture với Kafka giúp decouple các components trong AI platform của bạn.

Trả lời: Producers ghi sự kiện vào Kafka, consumers xử lý bất đồng bộ — tách rời luồng, dễ scale và chịu lỗi tốt hơn.

4. Bạn đã implement observability như thế nào? Logs, metrics, và traces được thu thập và visualized ra sao?

Trả lời: Prometheus scrape `/metrics` (api-gateway, prefect); Grafana đọc từ Prometheus (đã thêm datasource); traces gửi tới LangSmith.

5. Nếu một service trong stack (ví dụ: Qdrant hoặc Kafka) bị crash, hệ thống của bạn sẽ xử lý như thế nào? Có graceful degradation không?

Trả lời: Có — Kafka giữ buffer, Prefect dùng retries và backoff, Docker restart policies + persistent volumes cho phục hồi.