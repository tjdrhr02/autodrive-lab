FROM python:3.11-slim

WORKDIR /app

# 런타임 기본값(운영 친화)
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# non-root 실행을 위한 유저 생성
RUN addgroup --system app && adduser --system --ingroup app --home /home/app app

# Layer cache 최적화: requirements 먼저 복사 후 설치
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 앱 소스 복사 (모듈 분리된 파일들 포함)
COPY . /app

# 파일 권한 정리 후 non-root로 전환
RUN chown -R app:app /app
USER app

ENV PORT=8000
EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

