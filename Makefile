.PHONY: up down logs client-install client-run curl-health curl-infer

COMPOSE = docker compose -f infra/docker-compose.yml

up:
	$(COMPOSE) up --build

down:
	$(COMPOSE) down

logs:
	$(COMPOSE) logs -f

client-install:
	python3 -m pip install -r client/requirements.txt

client-run:
	python3 client/client.py

curl-health:
	curl -sS http://localhost:$${PORT:-8000}/health | python3 -m json.tool

curl-infer:
	REQ_ID=$$(python3 -c 'import uuid; print(uuid.uuid4())'); \
	TS_MS=$$(python3 -c 'import time; print(int(time.time()*1000))'); \
	curl -sS -X POST http://localhost:$${PORT:-8000}/infer \
	  -H 'Content-Type: application/json' \
	  -d "{\"request_id\":\"$${REQ_ID}\",\"ts_ms\":$${TS_MS},\"frame_meta\":{\"w\":320,\"h\":240},\"features\":[0.2,0.5,0.8]}" | python3 -m json.tool

