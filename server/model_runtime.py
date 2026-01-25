from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class Action(str, Enum):
    TURN_LEFT = "TURN_LEFT"
    TURN_RIGHT = "TURN_RIGHT"
    STRAIGHT = "STRAIGHT"


@dataclass(frozen=True)
class InferResult:
    action: Action
    steering: float  # -1.0 ~ 1.0
    confidence: float  # 0.0 ~ 1.0


class ModelRuntime(Protocol):
    def infer(self, features: list[float]) -> InferResult: ...


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


class RuleBasedRuntime:
    """
    Day 1 더미(규칙 기반) 런타임.

    요구사항:
    - features[0] > features[2] -> TURN_LEFT
    - features[2] > features[0] -> TURN_RIGHT
    - otherwise -> STRAIGHT
    - steering 값은 -1.0 ~ 1.0 범위로 매핑
    """

    def infer(self, features: list[float]) -> InferResult:
        if len(features) < 3:
            return InferResult(action=Action.STRAIGHT, steering=0.0, confidence=0.2)

        left = float(features[0])
        right = float(features[2])

        if left > right:
            action = Action.TURN_LEFT
        elif right > left:
            action = Action.TURN_RIGHT
        else:
            action = Action.STRAIGHT

        # steering: right-left를 [-1,1]로 클램프 (feature가 0~1이면 대략 -1~1)
        steering = _clamp(right - left, -1.0, 1.0)

        # confidence: 좌/우 차이의 절대값을 0~1로 클램프
        confidence = _clamp(abs(right - left), 0.0, 1.0)

        return InferResult(action=action, steering=steering, confidence=confidence)


class OnnxRuntimeRuntime:
    """
    2주차+를 위한 확장 포인트(ONNXRuntime).
    Day 1에는 기본 requirements에 onnxruntime을 넣지 않으므로, 없으면 에러를 던진다.
    """

    def __init__(self, model_path: str):
        try:
            import onnxruntime as ort  # type: ignore
        except ModuleNotFoundError as e:
            raise RuntimeError(
                "MODEL_RUNTIME=onnx 이지만 onnxruntime 패키지가 설치되어 있지 않습니다.\n"
                "Day 1 템플릿은 기본으로 rule 런타임을 사용합니다.\n"
                "원하면 서버 이미지에 onnxruntime을 추가 설치하세요."
            ) from e

        self._ort = ort
        self._sess = ort.InferenceSession(model_path, providers=["CPUExecutionProvider"])

    def infer(self, features: list[float]) -> InferResult:
        # 실제 모델 연결은 2주차+에서 구현 (입출력 텐서 규격 정의 필요)
        # 여기서는 뼈대만 제공한다.
        raise NotImplementedError("ONNX runtime inference is a Week 2+ task.")


def build_runtime(name: str) -> ModelRuntime:
    name = (name or "rule").lower()
    if name == "rule":
        return RuleBasedRuntime()
    if name == "onnx":
        # 모델 경로는 2주차+에서 확정. 지금은 placeholder.
        return OnnxRuntimeRuntime(model_path="/models/model.onnx")
    raise ValueError(f"Unknown MODEL_RUNTIME: {name}")

