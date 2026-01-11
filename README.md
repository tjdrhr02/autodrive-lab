## autodrive-lab (Day 1 템플릿)

“PC(Mac)에서 돌아가는 **OpenCV 클라이언트** → **Docker로만 실행되는 FastAPI 추론 서버**”의 최소 뼈대 템플릿입니다.  
1주차는 **실제 ML 모델 없이** 더미 추론으로도 끝까지 통신이 흐르도록 구성했습니다.

### 레포 구조

```text
autodrive-lab/
  README.md
  LICENSE
  .gitignore
  Makefile
  infra/
    docker-compose.yml
  server/
    Dockerfile
    requirements.txt
    app.py
  client/
    requirements.txt
    client.py
  docs/
    architecture.md
    api.md
```

---

## 사전 준비 (도커 초보 기준)

### 1) Docker 설치 확인

- Docker Desktop 설치 후, 아래가 정상 동작해야 합니다.

```bash
docker --version
docker compose version
```

### 2) (선택) `.env`로 설정 바꾸기

이 레포는 **`.env.example` 파일을 만들지 않습니다.** 대신 아래 내용을 참고해, 필요하면 프로젝트 루트에 `.env` 파일을 직접 만들어주세요.  
Docker Compose는 기본적으로 **프로젝트 루트의 `.env`**를 자동으로 읽습니다.

```bash
# .env (직접 생성)

# 호스트에 노출할 포트(기본 8000)
PORT=8000

# 서버 로그 레벨(기본 INFO): DEBUG/INFO/WARNING/ERROR
LOG_LEVEL=INFO

# 모델/서빙 버전 문자열(기본 v0)
MODEL_VERSION=v0

# (클라이언트용) 서버 URL (기본 http://localhost:8000)
SERVER_URL=http://localhost:8000
```

`.env`는 민감정보가 생길 수 있으니 `.gitignore`에 포함되어 있습니다.

---

## 로컬 실행 (서버는 compose로만!)

### 1) 서버 실행 (Docker Compose)

프로젝트 루트에서 아래 한 줄이면 됩니다.

```bash
make up
```

- 성공하면 `http://localhost:${PORT}`(기본 `8000`)에서 서버가 뜹니다.
- 서버는 요청마다 **request_id, latency_ms**를 stdout으로 출력합니다(컨테이너 로그로 확인).

### 2) 서버 상태 확인

```bash
make curl-health
```

예상 응답:

```json
{"ok":true,"version":"v0"}
```

### 3) 더미 추론 API 호출(샘플)

```bash
make curl-infer
```

---

## 클라이언트 실행 (Mac 웹캠 → /infer 호출)

클라이언트는 로컬 파이썬으로 실행합니다(웹캠 접근은 호스트에서 하는 게 편합니다).

### 1) 설치

```bash
make client-install
```

### 2) 실행

```bash
make client-run
```

- 실행하면 기본 웹캠(0번)에서 프레임을 읽고, 320x240으로 리사이즈 후 **좌/중/우 밝기 평균 3개 feature**를 만들어 `/infer`로 주기적으로 POST 합니다.
- 서버 응답의 **action/steering/confidence/latency_ms**가 콘솔 출력 + 화면 오버레이로 표시됩니다.
- `q` 키를 누르면 종료합니다.

---

## 자주 겪는 문제 (Troubleshooting)

### 포트 충돌 (이미 8000이 사용 중)

- 증상: `address already in use` / `Bind for 0.0.0.0:8000 failed`
- 해결: `.env`에서 `PORT`를 바꾸고 다시 실행

```bash
PORT=8010
make down
make up
```

### host 바인딩 이슈

- 컨테이너 내부 서버는 `0.0.0.0`로 바인딩해야 외부(호스트)에서 접근 가능합니다.
- 이 템플릿은 `uvicorn --host 0.0.0.0`로 이미 설정되어 있습니다.

### 컨테이너 로그 확인

```bash
make logs
```

서버는 각 `/infer` 요청마다 `request_id`, `latency_ms`, `action` 등을 stdout으로 찍습니다.

### 클라이언트에서 서버가 안 잡힘

- 기본은 `SERVER_URL=http://localhost:8000`
- 포트를 바꿨다면 `SERVER_URL`도 맞춰주세요.

```bash
SERVER_URL=http://localhost:8010 make client-run
```

---

## 다음 확장 아이디어 (2주차+)

1주차에는 외부 서비스(Redis/DB)를 넣지 않습니다. 아래는 확장 체크포인트만 적어둡니다.

- **ONNXRuntime**: 더미 로직 대신 ONNX 모델 로딩/추론 추가
- **GPU**: NVIDIA 환경에서는 CUDA 기반 이미지로 전환, Mac은 Metal(가능한 경우) 검토
- **클라우드 배포**: 환경변수/헬스체크/로그/리소스 제한/리버스 프록시(예: Nginx) 점검

자세한 내용은 `docs/architecture.md`, `docs/api.md`를 참고하세요.
