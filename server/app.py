import json
import logging
import time
from typing import Any, Literal

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field

from config import Settings
from model_runtime import build_runtime

settings = Settings.from_env()

logging.basicConfig(level=logging.INFO, format="%(message)s")
logger = logging.getLogger("autodrive-lab-server")
logger.setLevel(getattr(logging, settings.log_level, logging.INFO))

runtime = build_runtime(settings.model_runtime)

app = FastAPI(title="autodrive-lab", version=settings.model_version)


def _safe_json(body: bytes) -> dict[str, Any] | None:
    if not body:
        return None
    # Day 1 payload는 작으므로 64KB까지만 파싱
    if len(body) > 64 * 1024:
        return None
    try:
        return json.loads(body.decode("utf-8"))
    except Exception:
        return None


class FrameMeta(BaseModel):
    w: int = Field(..., ge=1)
    h: int = Field(..., ge=1)


class InferRequest(BaseModel):
    request_id: str
    ts_ms: int
    frame_meta: FrameMeta
    features: list[float] = Field(..., min_length=1)


class InferResponse(BaseModel):
    request_id: str
    action: Literal["TURN_LEFT", "TURN_RIGHT", "STRAIGHT"]
    steering: float
    confidence: float
    latency_ms: int
    model_version: str


@app.middleware("http")
async def request_access_log(request: Request, call_next):
    """
    최소 서빙 품질(요청당 단일 로그 라인):
    - latency(ms) 측정
    - request_id 기반 로그 추적 가능(가능하면 body JSON에서 추출)
    - 에러 발생 시 status_code + 로그 출력
    - stdout 로그 필드: request_id, latency_ms, action, model_version (+ status_code/path/method)
    """
    t0 = time.perf_counter()

    request_id = None
    # request_id는 body(JSON)에 들어오므로 미리 시도한다.
    # Starlette는 request.body()를 캐시하므로 이후 FastAPI 파싱에 영향이 적다.
    try:
        body = await request.body()
        parsed = _safe_json(body)
        if isinstance(parsed, dict):
            rid = parsed.get("request_id")
            if isinstance(rid, str) and rid:
                request_id = rid
    except Exception:
        request_id = None

    request.state.request_id = request_id
    request.state.action = None

    try:
        response = await call_next(request)
    except Exception:
        latency_ms = int((time.perf_counter() - t0) * 1000)
        logger.exception(
            {
                "request_id": request_id,
                "latency_ms": latency_ms,
                "action": getattr(request.state, "action", None),
                "model_version": settings.model_version,
                "status_code": 500,
                "path": request.url.path,
                "method": request.method,
            }
        )
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal Server Error", "request_id": request_id},
        )

    latency_ms = int((time.perf_counter() - t0) * 1000)
    action = getattr(request.state, "action", None)
    logger.info(
        {
            "request_id": request_id,
            "latency_ms": latency_ms,
            "action": action,
            "model_version": settings.model_version,
            "status_code": response.status_code,
            "path": request.url.path,
            "method": request.method,
        }
    )
    response.headers["x-request-id"] = request_id or ""
    return response


@app.get("/health")
def health(request: Request):
    request.state.action = "HEALTH"
    return {"ok": True, "version": settings.model_version}


@app.post("/infer", response_model=InferResponse)
def infer(req: InferRequest, request: Request):
    # /infer는 response schema에 latency_ms를 포함하므로 여기서도 측정한다.
    t0 = time.perf_counter()
    result = runtime.infer(req.features)
    latency_ms = int((time.perf_counter() - t0) * 1000)

    # middleware 로그에 action을 포함시키기 위한 공유
    request.state.action = result.action.value

    return InferResponse(
        request_id=req.request_id,
        action=result.action.value,
        steering=float(result.steering),
        confidence=float(result.confidence),
        latency_ms=latency_ms,
        model_version=settings.model_version,
    )

