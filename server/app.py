import logging
import os
import time
from enum import Enum
from typing import List, Literal, Optional

from fastapi import FastAPI
from pydantic import BaseModel, Field


def _get_env(name: str, default: str) -> str:
    v = os.getenv(name)
    return v if v is not None and v != "" else default


LOG_LEVEL = _get_env("LOG_LEVEL", "INFO").upper()
MODEL_VERSION = _get_env("MODEL_VERSION", "v0")

logging.basicConfig(
    level=getattr(logging, LOG_LEVEL, logging.INFO),
    format="%(message)s",
)
logger = logging.getLogger("autodrive-lab-server")

app = FastAPI(title="autodrive-lab", version=MODEL_VERSION)


class Action(str, Enum):
    TURN_LEFT = "TURN_LEFT"
    TURN_RIGHT = "TURN_RIGHT"
    STRAIGHT = "STRAIGHT"


class FrameMeta(BaseModel):
    w: int = Field(..., ge=1)
    h: int = Field(..., ge=1)


class InferRequest(BaseModel):
    request_id: str
    ts_ms: int
    frame_meta: FrameMeta
    features: List[float] = Field(..., min_length=1)


class InferResponse(BaseModel):
    request_id: str
    action: Literal["TURN_LEFT", "TURN_RIGHT", "STRAIGHT"]
    steering: float
    confidence: float
    latency_ms: int
    model_version: str


@app.get("/health")
def health():
    return {"ok": True, "version": MODEL_VERSION}


def _dummy_policy(features: List[float]) -> tuple[Action, float, float]:
    """
    Day 1 더미 추론:
    - client가 보내는 [left_mean, center_mean, right_mean] (0~1)을 가정
    - 더 밝은 방향으로 '간다'는 매우 단순한 규칙
    """
    if len(features) < 3:
        # 최소 구성: 중앙값만 있으면 직진
        return (Action.STRAIGHT, 0.0, 0.2)

    left, center, right = features[0], features[1], features[2]
    diff = float(right - left)  # +면 우회전, -면 좌회전

    steering = max(-1.0, min(1.0, diff))  # [-1, 1]로 클램프
    abs_diff = abs(diff)

    if abs_diff < 0.05:
        action = Action.STRAIGHT
    elif diff > 0:
        action = Action.TURN_RIGHT
    else:
        action = Action.TURN_LEFT

    # confidence: 단순히 좌/우 차이 기반 (0~1)
    confidence = max(0.0, min(1.0, abs_diff))

    # center가 너무 어두우면 confidence 낮추기(그냥 예시)
    if center < 0.2:
        confidence *= 0.7

    return (action, steering, confidence)


@app.post("/infer", response_model=InferResponse)
def infer(req: InferRequest):
    t0 = time.perf_counter()

    action, steering, confidence = _dummy_policy(req.features)

    latency_ms = int((time.perf_counter() - t0) * 1000)

    # 요청마다 stdout 로그: request_id, latency_ms 필수
    logger.info(
        {
            "event": "infer",
            "request_id": req.request_id,
            "latency_ms": latency_ms,
            "action": action.value,
            "model_version": MODEL_VERSION,
        }
    )

    return InferResponse(
        request_id=req.request_id,
        action=action.value,
        steering=float(steering),
        confidence=float(confidence),
        latency_ms=latency_ms,
        model_version=MODEL_VERSION,
    )

