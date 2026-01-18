## STUDY.md

## 이번주는 여행중..

이 문서는 `autodrive-lab` Day 1을 진행하면서 나왔던 질문/답변을 모아 둔 개인 학습 노트입니다.

---

## Q1) 개발자로써 개발 모드로 로컬에서 서버 띄우는 방법 vs 도커로 서버 띄우는 방법?

### A1-1) 로컬 “개발 모드”(Docker 없이)로 서버 실행

목적: **코드 수정 → 즉시 반영(핫리로드)**, 디버깅 편의.

```bash
cd server
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

# (선택) 환경변수
export PORT=8000
export LOG_LEVEL=DEBUG
export MODEL_VERSION=v0

uvicorn app:app --host 127.0.0.1 --port ${PORT:-8000} --reload
```

확인:

```bash
curl http://localhost:8000/health
```

### A1-2) Docker로 서버 실행(이 레포의 기본/권장)

목적: **환경 재현성 + 운영 형태(컨테이너) 그대로** 학습.

```bash
# 프로젝트 루트에서
make up
```

또는:

```bash
docker compose -f infra/docker-compose.yml up --build
```

확인:

```bash
make curl-health
```

---

## Q2) 로컬 개발 모드 vs Docker 실행 장단점 비교

### A2) 장단점

- **로컬 개발 모드 장점**
  - `--reload`로 코드 변경이 즉시 반영되어 빠름
  - IDE/디버거 붙이기 쉬움
  - “빌드” 과정이 없어서 반복 작업이 가벼움

- **로컬 개발 모드 단점**
  - 내 Mac 환경(파이썬 버전/패키지/OS)에 의존 → 다른 환경에서 재현 어려움
  - “컨테이너에서만 생기는 문제”를 놓치기 쉬움

- **Docker 실행 장점**
  - 실행 환경이 고정/재현 가능(팀/CI/배포로 이어짐)
  - 의존성 격리(로컬 파이썬 환경 오염 감소)
  - 포트/환경변수/재시작 정책/로그 등 운영 요소를 Day 1부터 체득하기 좋음

- **Docker 실행 단점**
  - 빌드/리빌드 시간이 듦
  - 기본 설정만으로는 핫리로드/로컬 디버깅이 로컬 실행보다 번거로움(추가 설정 필요)

---

## Q3) `infra/docker-compose.yml`과 `server/Dockerfile`은 무슨 역할? `.env`와의 차이는?

### A3-1) 역할 요약(한 문장)

- **`server/Dockerfile`**: 서버 이미지를 **어떻게 만들지**(베이스 이미지, 의존성 설치, 파일 복사, 기본 실행명령)를 정의
- **`infra/docker-compose.yml`**: 그 이미지를(또는 빌드해서) **어떻게 실행할지**(포트, 환경변수, 재시작 정책, 실행 커맨드)를 정의
- **`.env`(파일)**: `PORT`, `LOG_LEVEL` 같은 값을 **환경별로 바꾸기 위한 값 모음**(보통 git에 안 올림)

### A3-2) `.env`와의 역할 차이(비유)

- **Dockerfile**: “레고 블록(이미지) 자체를 만드는 레시피”
- **docker-compose.yml**: “레고 블록을 조립해서 실제로 켜는 방법”
- **.env**: “조립할 때 쓰는 옵션 값(포트/로그레벨/버전 문자열 등)”

---

## Q4) `infra/docker-compose.yml` 각 줄이 무슨 역할?

참고 파일: `infra/docker-compose.yml`

```yaml
services:                        # compose에서 실행할 컨테이너(서비스) 목록 시작
  server:                        # 서비스 이름(여기서는 server)
    build:                       # 이미지를 '빌드해서' 실행하겠다는 의미
      context: ./server          # 빌드 컨텍스트(이 디렉토리 기준으로 Dockerfile/파일 COPY)
      dockerfile: Dockerfile     # 사용할 Dockerfile 이름
    container_name: autodrive-lab-server  # 컨테이너 이름을 고정(기본 랜덤 이름 대신)
    restart: unless-stopped      # 크래시/재부팅 시 자동 재시작(사용자가 stop하면 재시작 안 함)
    environment:                 # 컨테이너 내부로 주입할 환경변수들
      - PORT=${PORT:-8000}       # 호스트 환경/루트 .env의 PORT를 쓰되 없으면 8000
      - LOG_LEVEL=${LOG_LEVEL:-INFO}      # 없으면 INFO
      - MODEL_VERSION=${MODEL_VERSION:-v0}# 없으면 v0
    ports:                       # 호스트:컨테이너 포트 매핑
      - "${PORT:-8000}:${PORT:-8000}"     # 예) 8000:8000 (호스트에서 localhost:8000로 접근)
    command: >                   # 이미지의 기본 CMD를 덮어써서 이 명령으로 실행
      uvicorn app:app --host 0.0.0.0 --port ${PORT:-8000} # 컨테이너 밖에서 접근 가능하게 0.0.0.0
```

---

## Q5) `server/Dockerfile` 각 줄이 무슨 역할?

참고 파일: `server/Dockerfile`

```dockerfile
FROM python:3.11-slim                     # 파이썬 3.11 기반의 최소 리눅스 이미지를 베이스로 사용
WORKDIR /app                              # 컨테이너 내부 작업 디렉토리를 /app으로 설정

# Layer cache 최적화: requirements 먼저 복사 후 설치
COPY requirements.txt /app/requirements.txt  # 의존성 목록만 먼저 복사(캐시 잘 타게)
RUN pip install --no-cache-dir -r /app/requirements.txt # 의존성 설치(이미지 레이어로 저장)

# 앱 소스 복사
COPY app.py /app/app.py                   # 서버 코드 파일 복사

ENV PORT=8000                             # 컨테이너 내부 기본 PORT 값(실제는 compose env로 덮일 수 있음)
EXPOSE 8000                               # 문서/메타데이터용(포트 오픈 자체는 아님)

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"] # 기본 실행 명령(compose command가 덮을 수 있음)
```

