"""
Realtime Face Recognition client.

This script streams webcam frames to the Identify API endpoint and overlays the
returned bounding boxes + metadata locally so that we can validate the end-to-end
AWS pipeline (API Gateway → Lambda → Rekognition/DynamoDB) without having to run
the desktop GUI.

Prerequisites:
    pip install opencv-python requests websocket-client

Usage:
    python samples/clients/realtime/realtime_face_recognition_client.py ^
        --api https://xxxxx.execute-api.ap-southeast-1.amazonaws.com/dev ^
        --camera 0 --interval 2 --threshold 0.6
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import sys
import threading
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from getpass import getpass
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse
import uuid

import boto3
import cv2  # type: ignore
import numpy as np  # type: ignore
import requests

try:
    import websocket  # type: ignore
except ImportError as exc:  # pragma: no cover
    websocket = None
    WS_IMPORT_ERROR = exc
else:
    WS_IMPORT_ERROR = None


DEFAULT_API_URL = os.getenv("FACE_API_URL", "http://localhost:8000")
DEFAULT_WS_URL = os.getenv("FACE_WS_URL", "")
DEFAULT_API_KEY = os.getenv("FACE_API_KEY", "")
DEFAULT_API_KEY_HEADER = os.getenv("FACE_API_KEY_HEADER", "x-api-key")
DEFAULT_ID_TOKEN = os.getenv("FACE_ID_TOKEN", "")
DEFAULT_CLIENT_ID = os.getenv("FACE_CLIENT_ID", "")
DEFAULT_TELEMETRY_URL = os.getenv("FACE_TELEMETRY_URL", "")


@dataclass
class IdentifiedFace:
    """Lightweight container for faces returned by the API."""

    user_name: str
    folder_name: str
    confidence: float
    location: Dict[str, float]
    gender: Optional[str] = None
    birth_year: Optional[int] = None
    hometown: Optional[str] = None
    residence: Optional[str] = None


class IdentificationError(RuntimeError):
    """Raised when the Identify API call fails."""


class RealtimeFaceRecognitionClient:
    """Streams frames to the Identify API and renders overlay locally."""

    def __init__(
        self,
        api_base_url: str,
        camera_index: int = 0,
        threshold: float = 0.6,
        interval: float = 2.0,
        timeout: float = 15.0,
        api_key: str | None = None,
        api_key_header: str = "x-api-key",
        transport: str = "rest",
        ws_url: Optional[str] = None,
        id_token: Optional[str] = None,
        client_id: Optional[str] = None,
        telemetry_enabled: bool = True,
        telemetry_url: Optional[str] = None,
    ) -> None:
        self.api_base_url = api_base_url.rstrip("/")
        self.camera_index = camera_index
        self.threshold = threshold
        self.interval = interval
        self.timeout = timeout
        self.api_key = api_key or ""
        self.api_key_header = api_key_header
        self.identify_endpoint = self._resolve_endpoint(api_base_url)
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "RealtimeFaceClient/1.0"})
        if self.api_key:
            self.session.headers[self.api_key_header] = self.api_key

        self._last_request_ts = 0.0
        self._latest_faces: List[IdentifiedFace] = []
        self._latest_latency_ms: Optional[float] = None
        self._status_message = "Waiting for first frame…"
        self.transport = transport
        self._pending_latency_start: Optional[float] = None
        self.ws_client: Optional[WebSocketTransport] = None
        self.id_token = id_token
        if self.id_token:
            self.session.headers["Authorization"] = f"Bearer {self.id_token}"
        self.client_id = client_id or DEFAULT_CLIENT_ID or f"cli-{uuid.uuid4().hex[:8]}"
        self.telemetry_enabled = telemetry_enabled
        self.telemetry_endpoint = (
            telemetry_url
            or DEFAULT_TELEMETRY_URL
            or self._resolve_telemetry_endpoint(api_base_url)
        )

        if self.transport == "websocket":
            if WS_IMPORT_ERROR is not None:
                raise RuntimeError(
                    "websocket-client dependency missing. Install via pip install websocket-client"
                ) from WS_IMPORT_ERROR
            ws_target = ws_url or self._derive_websocket_url(api_base_url)
            headers = []
            if self.api_key:
                headers.append(f"{self.api_key_header}: {self.api_key}")
            if self.id_token:
                headers.append(f"Authorization: Bearer {self.id_token}")
            self.ws_client = WebSocketTransport(
                url=ws_target,
                headers=headers,
                message_callback=self._handle_ws_message,
            )
            self._status_message = (
                "WebSocket connected. Streaming disabled until first frame."
            )

    def _resolve_endpoint(self, base_url: str) -> str:
        if base_url.endswith("/identify"):
            return base_url
        if base_url.endswith("/api/v1"):
            return f"{base_url}/identify"
        if "/api/v1/identify" in base_url:
            return base_url
        return f"{base_url}/api/v1/identify"

    def _resolve_telemetry_endpoint(self, base_url: str) -> str:
        trimmed = base_url.rstrip("/")
        if not trimmed:
            return "http://localhost:8000/api/v1/telemetry"
        if trimmed.endswith("/telemetry"):
            return trimmed
        if trimmed.endswith("/api/v1"):
            return f"{trimmed}/telemetry"
        if "/api/v1/" in trimmed:
            prefix = trimmed.split("/api/v1")[0]
            return f"{prefix}/api/v1/telemetry"
        return f"{trimmed}/api/v1/telemetry"

    def _serialize_frame(self, frame: np.ndarray) -> bytes:
        success, buffer = cv2.imencode(
            ".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), 90]
        )
        if not success:
            raise IdentificationError("Failed to encode frame as JPEG")
        return buffer.tobytes()

    def _send_telemetry(
        self,
        *,
        status: str,
        latency_ms: Optional[float] = None,
        faces_detected: int = 0,
        error_message: Optional[str] = None,
    ) -> None:
        if not self.telemetry_enabled or not self.telemetry_endpoint:
            return
        payload = {
            "client_id": self.client_id,
            "transport": self.transport,
            "latency_ms": latency_ms,
            "faces_detected": faces_detected,
            "status": status,
            "error_message": error_message,
            "api_endpoint": self.identify_endpoint,
            "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "interval_seconds": self.interval,
        }
        headers = {}
        if self.api_key:
            headers[self.api_key_header] = self.api_key
        if self.id_token:
            headers["Authorization"] = f"Bearer {self.id_token}"
        try:
            self.session.post(
                self.telemetry_endpoint,
                json=payload,
                headers=headers,
                timeout=5,
            )
        except Exception:
            # Telemetry errors must not interrupt main loop
            pass

    def _call_identify_api(self, frame: np.ndarray) -> List[IdentifiedFace]:
        payload = self._serialize_frame(frame)
        files = {"image": ("frame.jpg", payload, "image/jpeg")}
        data = {"threshold": str(self.threshold)}

        response = self.session.post(
            self.identify_endpoint,
            files=files,
            data=data,
            timeout=self.timeout,
        )
        if response.status_code >= 400:
            raise IdentificationError(
                f"Identify API failed: {response.status_code} {response.text}"
            )
        body = response.json()
        faces = [
            IdentifiedFace(
                user_name=face.get("user_name") or face.get("folder_name", "Unknown"),
                folder_name=face.get("folder_name", "Unknown"),
                confidence=float(face.get("confidence", 0.0)),
                location=face.get("location", {}),
                gender=face.get("gender"),
                birth_year=face.get("birth_year"),
                hometown=face.get("hometown"),
                residence=face.get("residence"),
            )
            for face in body.get("faces", [])
        ]
        return faces

    def _maybe_refresh_results(self, frame: np.ndarray) -> None:
        now = time.time()
        if now - self._last_request_ts < self.interval:
            return
        self._last_request_ts = now

        start_call = time.time()
        try:
            faces = self._call_identify_api(frame)
            self._latest_faces = faces
            self._latest_latency_ms = (time.time() - start_call) * 1000.0
            self._status_message = (
                f"{len(faces)} face(s) · {self._latest_latency_ms:.0f} ms latency"
            )
            self._send_telemetry(
                status="success",
                latency_ms=self._latest_latency_ms,
                faces_detected=len(faces),
            )
        except Exception as err:  # pylint: disable=broad-except
            self._status_message = f"API error: {err}"
            self._send_telemetry(status="error", error_message=str(err))

    def _maybe_stream_websocket(self, frame: np.ndarray) -> None:
        if not self.ws_client:
            return
        now = time.time()
        if now - self._last_request_ts < self.interval:
            return
        self._last_request_ts = now
        try:
            payload = base64.b64encode(self._serialize_frame(frame)).decode("ascii")
            self._pending_latency_start = now
            self.ws_client.send_frame(
                {
                    "action": "identify",
                    "image_base64": payload,
                    "threshold": self.threshold,
                    **({"token": self.id_token} if self.id_token else {}),
                }
            )
            self._status_message = "Frame sent via WebSocket…"
        except Exception as err:  # pylint: disable=broad-except
            self._status_message = f"WS error: {err}"
            self._send_telemetry(status="error", error_message=str(err))

    def _handle_ws_message(self, payload: Dict[str, Any]) -> None:
        faces_payload: List[IdentifiedFace] = []
        if "faces" in payload:
            faces_payload = [
                IdentifiedFace(
                    user_name=face.get("user_name")
                    or face.get("folder_name", "Unknown"),
                    folder_name=face.get("folder_name", "Unknown"),
                    confidence=float(face.get("confidence", 0.0)),
                    location=face.get("location", {}),
                )
                for face in payload.get("faces", [])
            ]
        elif "matches" in payload:
            faces_payload = [
                IdentifiedFace(
                    user_name=match.get("user_id", "Unknown"),
                    folder_name=match.get("user_id", "Unknown"),
                    confidence=float(match.get("confidence", 0.0)),
                    location={},
                )
                for match in payload.get("matches", [])
            ]
        else:
            self._status_message = payload.get("message", "No matches")
            self._send_telemetry(
                status="info",
                error_message=payload.get("error") or payload.get("message"),
            )
            return

        self._latest_faces = faces_payload
        if self._pending_latency_start:
            self._latest_latency_ms = (
                time.time() - self._pending_latency_start
            ) * 1000.0
        self._status_message = (
            f"{len(faces_payload)} face(s) · "
            f"{(self._latest_latency_ms or 0):.0f} ms latency (WebSocket)"
        )
        self._pending_latency_start = None
        self._send_telemetry(
            status="success",
            latency_ms=self._latest_latency_ms,
            faces_detected=len(faces_payload),
        )

    def _derive_websocket_url(self, base_http_url: str) -> str:
        if base_http_url.startswith("ws://") or base_http_url.startswith("wss://"):
            return base_http_url
        trimmed = base_http_url.rstrip("/")
        if trimmed.endswith("/api/v1"):
            trimmed = trimmed[: -len("/api/v1")]
        if trimmed.startswith("https://"):
            trimmed = "wss://" + trimmed[len("https://") :]
        elif trimmed.startswith("http://"):
            trimmed = "ws://" + trimmed[len("http://") :]
        if self.id_token:
            separator = "&" if "?" in trimmed else "?"
            return f"{trimmed}{separator}token={self.id_token}"
        return trimmed

    def _draw_overlay(self, frame: np.ndarray) -> np.ndarray:
        overlay = frame.copy()
        for face in self._latest_faces:
            location = face.location or {}
            top = int(location.get("top", 0))
            right = int(location.get("right", 0))
            bottom = int(location.get("bottom", 0))
            left = int(location.get("left", 0))
            cv2.rectangle(overlay, (left, top), (right, bottom), (0, 255, 0), 2)
            label = f"{face.user_name} ({face.confidence*100:.1f}%)"
            cv2.putText(
                overlay,
                label,
                (left, max(20, top - 10)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.5,
                (0, 255, 0),
                1,
                cv2.LINE_AA,
            )

        footer = self._status_message
        cv2.rectangle(
            overlay,
            (0, overlay.shape[0] - 30),
            (overlay.shape[1], overlay.shape[0]),
            (0, 0, 0),
            -1,
        )
        cv2.putText(
            overlay,
            footer,
            (10, overlay.shape[0] - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.5,
            (255, 255, 255),
            1,
            cv2.LINE_AA,
        )
        return overlay

    def run(self) -> None:
        cap = cv2.VideoCapture(self.camera_index)
        if not cap.isOpened():
            raise RuntimeError(f"Cannot open camera index {self.camera_index}")

        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    self._status_message = "Unable to read from camera"
                    break

                if self.transport == "websocket":
                    self._maybe_stream_websocket(frame)
                else:
                    self._maybe_refresh_results(frame)
                frame_with_overlay = self._draw_overlay(frame)
                cv2.imshow("Realtime Face Recognition", frame_with_overlay)

                key = cv2.waitKey(1) & 0xFF
                if key == ord("q"):
                    break
                if key == ord("s"):
                    timestamp = int(time.time())
                    path = f"capture_{timestamp}.jpg"
                    cv2.imwrite(path, frame)
                    self._status_message = f"Saved frame to {path}"
        finally:
            cap.release()
            cv2.destroyAllWindows()
            if self.ws_client:
                self.ws_client.close()


class WebSocketTransport:
    """Simple wrapper around websocket-client for sending frames."""

    def __init__(self, url: str, headers: List[str], message_callback) -> None:
        if websocket is None:
            raise RuntimeError("websocket-client library not available")
        self._url = url
        self._headers = headers
        self._message_callback = message_callback
        self._ws_app = websocket.WebSocketApp(  # type: ignore
            url,
            header=headers,
            on_open=self._on_open,
            on_close=self._on_close,
            on_error=self._on_error,
            on_message=self._on_message,
        )
        self._connected = threading.Event()
        self._closed = False
        self._thread = threading.Thread(target=self._ws_app.run_forever, daemon=True)
        self._thread.start()
        if not self._connected.wait(timeout=10):
            raise RuntimeError("Unable to establish WebSocket connection")

    def send_frame(self, payload: Dict[str, Any]) -> None:
        if self._closed:
            raise RuntimeError("WebSocket connection closed")
        self._ws_app.send(json.dumps(payload))

    def close(self) -> None:
        self._closed = True
        try:
            self._ws_app.close()
        except Exception:  # pylint: disable=broad-except
            pass

    # WebSocket callbacks
    def _on_open(self, *_args) -> None:
        self._connected.set()

    def _on_close(self, *_args) -> None:
        self._connected.clear()

    def _on_error(self, *_args) -> None:
        self._connected.clear()

    def _on_message(self, _ws, message: str) -> None:
        try:
            data = json.loads(message)
        except json.JSONDecodeError:
            data = {"raw": message}
        self._message_callback(data)


def parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Realtime Face Recognition client for AWS stack"
    )
    parser.add_argument(
        "--api",
        dest="api_url",
        default=DEFAULT_API_URL,
        help="Base API URL (e.g. https://xxx.execute-api.amazonaws.com/dev)",
    )
    parser.add_argument(
        "--camera",
        dest="camera_index",
        type=int,
        default=0,
        help="OpenCV camera index (default: 0)",
    )
    parser.add_argument(
        "--threshold",
        dest="threshold",
        type=float,
        default=0.6,
        help="Recognition threshold passed to the API (0.0-1.0)",
    )
    parser.add_argument(
        "--interval",
        dest="interval",
        type=float,
        default=2.0,
        help="Seconds between API calls (default: 2 seconds)",
    )
    parser.add_argument(
        "--timeout",
        dest="timeout",
        type=float,
        default=15.0,
        help="HTTP timeout in seconds",
    )
    parser.add_argument(
        "--api-key",
        dest="api_key",
        default=DEFAULT_API_KEY,
        help="Optional API key to send with each request (FACE_API_KEY env)",
    )
    parser.add_argument(
        "--api-key-header",
        dest="api_key_header",
        default=DEFAULT_API_KEY_HEADER,
        help="Header name for the API key (FACE_API_KEY_HEADER env)",
    )
    parser.add_argument(
        "--transport",
        dest="transport",
        choices=["rest", "websocket"],
        default="rest",
        help="Transport mode: REST polling or WebSocket streaming",
    )
    parser.add_argument(
        "--ws-url",
        dest="ws_url",
        default=DEFAULT_WS_URL,
        help="Explicit WebSocket URL (defaults derived from --api)",
    )
    parser.add_argument(
        "--id-token",
        dest="id_token",
        default=DEFAULT_ID_TOKEN,
        help="Cognito ID token to use for Authorization (FACE_ID_TOKEN env)",
    )
    parser.add_argument(
        "--cognito-region",
        dest="cognito_region",
        default=None,
        help="Cognito region (auto-detected from API URL if omitted)",
    )
    parser.add_argument(
        "--cognito-user-pool-id",
        dest="cognito_user_pool_id",
        default=None,
        help="Cognito User Pool ID (optional, for documentation)",
    )
    parser.add_argument(
        "--cognito-client-id",
        dest="cognito_client_id",
        default=None,
        help="Cognito App Client ID (required if using username/password login)",
    )
    parser.add_argument(
        "--username",
        dest="username",
        default=None,
        help="Cognito username (will prompt for password)",
    )
    parser.add_argument(
        "--client-id",
        dest="client_id",
        default=DEFAULT_CLIENT_ID or None,
        help="Optional client identifier for telemetry",
    )
    parser.add_argument(
        "--disable-telemetry",
        dest="disable_telemetry",
        action="store_true",
        help="Disable telemetry uploads",
    )
    parser.add_argument(
        "--telemetry-url",
        dest="telemetry_url",
        default=DEFAULT_TELEMETRY_URL or None,
        help="Override telemetry endpoint (defaults derived from API URL)",
    )
    return parser.parse_args(argv)


def obtain_cognito_token(client_id: str, username: str, region: str) -> Optional[str]:
    """Authenticate against Cognito using USER_PASSWORD_AUTH."""
    password = getpass(f"Cognito password for {username}: ")
    if not password:
        return None
    client = boto3.client("cognito-idp", region_name=region)
    response = client.initiate_auth(
        ClientId=client_id,
        AuthFlow="USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": username, "PASSWORD": password},
    )
    return response.get("AuthenticationResult", {}).get("IdToken")


def _infer_region(args: argparse.Namespace) -> str:
    if args.cognito_region:
        return args.cognito_region
    parsed = urlparse(args.api_url)
    host = parsed.netloc or parsed.path
    if ".execute-api." in host:
        try:
            return host.split(".execute-api.")[1].split(".")[0]
        except IndexError:
            return "ap-southeast-1"
    return "ap-southeast-1"


def main(argv: Optional[List[str]] = None) -> int:
    args = parse_args(argv)
    id_token = args.id_token
    if not id_token and args.cognito_client_id and args.username:
        id_token = obtain_cognito_token(
            client_id=args.cognito_client_id,
            username=args.username,
            region=_infer_region(args),
        )
    client = RealtimeFaceRecognitionClient(
        api_base_url=args.api_url,
        camera_index=args.camera_index,
        threshold=args.threshold,
        interval=args.interval,
        timeout=args.timeout,
        api_key=args.api_key,
        api_key_header=args.api_key_header,
        transport=args.transport,
        ws_url=args.ws_url or None,
        id_token=id_token or None,
        client_id=args.client_id,
        telemetry_enabled=not args.disable_telemetry,
        telemetry_url=args.telemetry_url or None,
    )
    try:
        client.run()
    except KeyboardInterrupt:
        print("Interrupted by user.")
    except Exception as exc:  # pylint: disable=broad-except
        print(f"Fatal error: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
