FROM python:3.11-slim

WORKDIR /app

# Layer cache 최적화: requirements 먼저 복사 후 설치
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# 앱 소스 복사
COPY app.py /app/app.py

ENV PORT=8000
EXPOSE 8000

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8000"]

