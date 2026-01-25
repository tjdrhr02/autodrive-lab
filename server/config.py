import os
from dataclasses import dataclass


def _get_env(name: str, default: str | None = None) -> str | None:
    v = os.getenv(name)
    if v is None or v == "":
        return default
    return v


@dataclass(frozen=True)
class Settings:
    """
    서버 설정은 환경변수로 주입한다.

    - PORT: Uvicorn이 바인딩할 포트 (compose에서 사용)
    - LOG_LEVEL: DEBUG/INFO/WARNING/ERROR
    - MODEL_VERSION: 응답/로그에 포함할 모델(서빙) 버전 문자열
    - MODEL_RUNTIME: rule|onnx (기본 rule)
    """

    port: int
    log_level: str
    model_version: str
    model_runtime: str

    @classmethod
    def from_env(cls) -> "Settings":
        port_s = _get_env("PORT", "8000")
        log_level = (_get_env("LOG_LEVEL", "INFO") or "INFO").upper()
        model_version = _get_env("MODEL_VERSION", "v0") or "v0"
        model_runtime = (_get_env("MODEL_RUNTIME", "rule") or "rule").lower()

        try:
            port = int(port_s) if port_s is not None else 8000
        except ValueError:
            port = 8000

        return cls(
            port=port,
            log_level=log_level,
            model_version=model_version,
            model_runtime=model_runtime,
        )

