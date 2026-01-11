import os
import time
import uuid

import cv2
import numpy as np
import requests


def _get_env(name: str, default: str) -> str:
    v = os.getenv(name)
    return v if v is not None and v != "" else default


SERVER_URL = _get_env("SERVER_URL", "http://localhost:8000").rstrip("/")
INFER_URL = f"{SERVER_URL}/infer"

CAP_INDEX = int(_get_env("CAMERA_INDEX", "0"))
SEND_EVERY_MS = int(_get_env("SEND_EVERY_MS", "300"))  # 너무 자주 보내지 않도록 기본 300ms

RESIZE_W = int(_get_env("FRAME_W", "320"))
RESIZE_H = int(_get_env("FRAME_H", "240"))


def extract_features(frame_bgr: np.ndarray) -> list[float]:
    """
    Day 1 feature 예시:
    - frame을 320x240으로 리사이즈
    - grayscale로 변환
    - 좌/중/우 3구역의 밝기 평균을 0~1 float로 전송
    """
    resized = cv2.resize(frame_bgr, (RESIZE_W, RESIZE_H), interpolation=cv2.INTER_AREA)
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)

    third = RESIZE_W // 3
    left = gray[:, :third]
    center = gray[:, third : 2 * third]
    right = gray[:, 2 * third :]

    feats = [
        float(np.mean(left) / 255.0),
        float(np.mean(center) / 255.0),
        float(np.mean(right) / 255.0),
    ]
    return feats


def overlay_text(frame_bgr: np.ndarray, lines: list[str]) -> None:
    y = 24
    for line in lines:
        cv2.putText(
            frame_bgr,
            line,
            (12, y),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.6,
            (0, 255, 0),
            2,
            cv2.LINE_AA,
        )
        y += 24


def main() -> None:
    print(f"[client] SERVER_URL={SERVER_URL}")
    print(f"[client] INFER_URL={INFER_URL}")
    print(f"[client] CAMERA_INDEX={CAP_INDEX}, SEND_EVERY_MS={SEND_EVERY_MS}")

    cap = cv2.VideoCapture(CAP_INDEX)
    if not cap.isOpened():
        raise RuntimeError(
            "웹캠을 열 수 없습니다. 다른 앱(Zoom/Meet 등)이 점유 중인지 확인하거나 CAMERA_INDEX를 바꿔보세요."
        )

    last_send_ms = 0
    last_resp = None

    while True:
        ok, frame = cap.read()
        if not ok:
            print("[client] frame read failed; retrying...")
            time.sleep(0.05)
            continue

        now_ms = int(time.time() * 1000)
        if now_ms - last_send_ms >= SEND_EVERY_MS:
            request_id = str(uuid.uuid4())
            feats = extract_features(frame)

            payload = {
                "request_id": request_id,
                "ts_ms": now_ms,
                "frame_meta": {"w": RESIZE_W, "h": RESIZE_H},
                "features": feats,
            }

            try:
                t0 = time.perf_counter()
                r = requests.post(INFER_URL, json=payload, timeout=2.0)
                dt_ms = int((time.perf_counter() - t0) * 1000)
                r.raise_for_status()
                last_resp = r.json()

                print(
                    f"[infer] request_id={last_resp.get('request_id')} "
                    f"action={last_resp.get('action')} steering={last_resp.get('steering')} "
                    f"conf={last_resp.get('confidence')} latency_ms={last_resp.get('latency_ms')} "
                    f"(http_ms={dt_ms})"
                )
            except Exception as e:
                last_resp = {"error": str(e)}
                print(f"[infer] error: {e}")

            last_send_ms = now_ms

        lines = [
            f"SERVER: {SERVER_URL}",
            "q: quit",
        ]
        if isinstance(last_resp, dict) and "error" in last_resp:
            lines.append(f"ERROR: {last_resp['error'][:60]}")
        elif isinstance(last_resp, dict) and last_resp:
            lines.append(f"action: {last_resp.get('action')}")
            lines.append(f"steering: {last_resp.get('steering')}")
            lines.append(f"confidence: {last_resp.get('confidence')}")
            lines.append(f"latency_ms: {last_resp.get('latency_ms')}")

        overlay_text(frame, lines)
        cv2.imshow("autodrive-lab client", frame)

        key = cv2.waitKey(1) & 0xFF
        if key == ord("q"):
            break

    cap.release()
    cv2.destroyAllWindows()


if __name__ == "__main__":
    main()

