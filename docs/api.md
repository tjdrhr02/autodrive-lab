## API

Base URL: `http://localhost:${PORT}` (기본 8000)

---

### GET /health

응답:

```json
{
  "ok": true,
  "version": "v0"
}
```

---

### POST /infer

request(JSON):

```json
{
  "request_id": "uuid-string",
  "ts_ms": 1700000000000,
  "frame_meta": { "w": 640, "h": 480 },
  "features": [0.12, 0.34, 0.56]
}
```

response(JSON):

```json
{
  "request_id": "uuid-string",
  "action": "TURN_LEFT|TURN_RIGHT|STRAIGHT",
  "steering": 0.42,
  "confidence": 0.8,
  "latency_ms": 3,
  "model_version": "v0"
}
```

notes:

- `request_id`: client가 생성(uuid4)
- `features`: Day 1에서는 [left_mean, center_mean, right_mean] (0~1)
- `latency_ms`: 서버 내부 처리 시간(단순 정책 + 직렬화 포함)

