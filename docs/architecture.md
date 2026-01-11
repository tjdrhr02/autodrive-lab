## Architecture (Day 1)

### 목표

PC(Mac)에서 동작하는 **클라이언트(OpenCV)** 가 웹캠 프레임에서 간단한 feature를 만들고,  
Docker 컨테이너로 실행되는 **FastAPI 서버**에 `/infer` 요청을 보내 응답(action/steering 등)을 받아 화면에 오버레이합니다.

### 구성 요소

- **client (host python)**
  - Mac 기본 웹캠(기본 index=0)에서 프레임 읽기
  - 프레임 리사이즈(기본 320x240)
  - feature 추출(좌/중/우 3구역 밝기 평균)
  - `/infer`로 주기적 POST
  - 응답을 콘솔 출력 + 프레임 오버레이

- **server (docker compose)**
  - FastAPI + Uvicorn
  - `GET /health` : 헬스체크
  - `POST /infer` : 더미 정책 기반 action/steering 반환
  - 요청마다 stdout 로그에 request_id, latency_ms 출력

### 데이터 흐름

1. client가 프레임에서 feature([left, center, right]) 생성
2. client가 JSON을 `/infer`로 POST
3. server가 더미 정책으로 action/steering/confidence 산출
4. server가 latency_ms를 계산하고 응답 + 로그 출력
5. client가 응답을 콘솔 + 화면에 표시

### 확장 포인트(2주차+)

- `/infer` 내부의 더미 정책을 실제 모델(예: ONNXRuntime)로 교체
- feature를 raw frame(or JPEG) 업로드로 변경 (네트워크/지연/비용 고려)
- 배포 환경에 맞춘 healthcheck/observability/리소스 제한 추가

