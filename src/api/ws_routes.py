"""
WebSocket routes — real-time streaming + request queue.

Endpoints:
  WS  /ws/chat               - WebSocket chat with real-time streaming
  GET /api/queue/status       - Request queue status
  POST /api/queue/cancel/{id} - Cancel a queued request
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from pydantic import BaseModel

from src.config import Config
from src.log import setup_logging

log = setup_logging("ws_routes")

ws_router = APIRouter(tags=["websocket"])


# ── Request Queue ─────────────────────────────────────────────

class Priority(int, Enum):
    LOW = 0
    NORMAL = 1
    HIGH = 2
    CRITICAL = 3


@dataclass
class QueuedRequest:
    id: str = field(default_factory=lambda: uuid.uuid4().hex[:12])
    message: str = ""
    model: str = ""
    priority: Priority = Priority.NORMAL
    status: str = "queued"  # queued, processing, completed, failed, cancelled
    result: str = ""
    error: str = ""
    created_at: float = field(default_factory=time.time)
    started_at: float = 0.0
    completed_at: float = 0.0
    callback: asyncio.Future | None = None


class RequestQueue:
    """Priority queue for chat requests with backpressure."""

    def __init__(self, max_concurrent: int = 1):
        self._max_concurrent = max_concurrent
        self._queue: asyncio.PriorityQueue = asyncio.PriorityQueue()
        self._active: int = 0
        self._requests: dict[str, QueuedRequest] = {}
        self._lock = asyncio.Lock()

    async def enqueue(self, request: QueuedRequest) -> str:
        """Add request to queue. Returns request ID."""
        async with self._lock:
            self._requests[request.id] = request
            # Priority queue uses (priority, request_id) tuples
            # Lower number = higher priority (Priority.CRITICAL = 3 is highest)
            await self._queue.put((-request.priority.value, request.id))
        log.info(
            f"Queue: enqueued {request.id} (priority={request.priority.name}, "
            f"queue_size={self._queue.qsize()})"
        )
        return request.id

    async def process_next(self, process_fn):
        """Process next request from queue."""
        if self._active >= self._max_concurrent:
            return None

        try:
            priority, request_id = self._queue.get_nowait()
        except asyncio.QueueEmpty:
            return None

        request = self._requests.get(request_id)
        if not request or request.status == "cancelled":
            return None

        async with self._lock:
            self._active += 1

        request.status = "processing"
        request.started_at = time.time()

        try:
            result = await process_fn(request)
            request.result = result
            request.status = "completed"
        except Exception as e:
            request.error = str(e)
            request.status = "failed"
        finally:
            request.completed_at = time.time()
            async with self._lock:
                self._active -= 1

        return request

    def cancel(self, request_id: str) -> bool:
        """Cancel a queued request."""
        request = self._requests.get(request_id)
        if not request:
            return False
        if request.status == "queued":
            request.status = "cancelled"
            return True
        return False

    def get_status(self) -> dict:
        """Get queue status."""
        return {
            "queue_size": self._queue.qsize(),
            "active": self._active,
            "max_concurrent": self._max_concurrent,
            "requests": {
                rid: {
                    "id": r.id,
                    "status": r.status,
                    "priority": r.priority.name,
                    "created_at": r.created_at,
                    "elapsed": time.time() - r.created_at if r.status in ("queued", "processing") else 0,
                }
                for rid, r in list(self._requests.items())[-20:]  # Last 20
            },
        }


# Global queue instance
_queue = RequestQueue(max_concurrent=Config.POOL_SIZE or 1)


def get_queue() -> RequestQueue:
    return _queue


# ── WebSocket Chat ────────────────────────────────────────────

# Global references — set by server.py
_client = None
_pool = None
_lock = asyncio.Lock()


def set_ws_references(client, pool) -> None:
    global _client, _pool
    _client = client
    _pool = pool


@ws_router.websocket("/ws/chat")
async def websocket_chat(websocket: WebSocket):
    """
    WebSocket endpoint for real-time chat.

    Client sends JSON:
        {"type": "chat", "message": "...", "model": "...", "priority": "normal"}
        {"type": "ping"}
        {"type": "queue_status"}

    Server sends JSON:
        {"type": "thinking", "message": "..."}
        {"type": "chunk", "content": "..."}
        {"type": "complete", "message": "...", "response_time_ms": 1234}
        {"type": "error", "message": "..."}
        {"type": "pong"}
        {"type": "queue_status", ...}
    """
    await websocket.accept()
    log.info(f"WebSocket connected from {websocket.client}")

    # Send welcome
    await websocket.send_json({
        "type": "welcome",
        "provider": Config.PROVIDER,
        "model": Config.default_model(),
    })

    try:
        while True:
            data = await websocket.receive_text()
            msg = json.loads(data)

            msg_type = msg.get("type", "")

            if msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            elif msg_type == "queue_status":
                await websocket.send_json({
                    "type": "queue_status",
                    **_queue.get_status(),
                })

            elif msg_type == "chat":
                text = msg.get("message", "")
                model = msg.get("model", "")
                priority_str = msg.get("priority", "normal")
                priority_map = {
                    "low": Priority.LOW,
                    "normal": Priority.NORMAL,
                    "high": Priority.HIGH,
                    "critical": Priority.CRITICAL,
                }
                priority = priority_map.get(priority_str, Priority.NORMAL)

                if not text:
                    await websocket.send_json({
                        "type": "error",
                        "message": "Empty message",
                    })
                    continue

                # Send thinking indicator
                await websocket.send_json({
                    "type": "thinking",
                    "message": "Processing your message...",
                })

                # Queue the request
                request = QueuedRequest(
                    message=text,
                    model=model,
                    priority=priority,
                )

                request_id = await _queue.enqueue(request)

                # Process (wait for result)
                async def process_fn(req):
                    from src.api.openai_routes import _do_chat_completion, _build_prompt, ChatMessage
                    from src.chatgpt.models import ChatResponse

                    # Build client-side ChatMessage
                    messages = [ChatMessage(role="user", content=req.message)]

                    if req.model and _client and hasattr(_client, "select_model"):
                        await _client.select_model(req.model)

                    if _client:
                        result = await _client.send_message(req.message)
                        return result.message
                    else:
                        raise RuntimeError("No client available")

                # Process the request
                result = await _queue.process_next(process_fn)

                if result and result.status == "completed":
                    # Stream the response in chunks
                    response_text = result.result
                    words = response_text.split(" ")
                    chunk_size = 3

                    for i in range(0, len(words), chunk_size):
                        chunk = " ".join(words[i:i + chunk_size])
                        if i > 0:
                            chunk = " " + chunk
                        await websocket.send_json({
                            "type": "chunk",
                            "content": chunk,
                        })
                        await asyncio.sleep(0.02)

                    await websocket.send_json({
                        "type": "complete",
                        "message": response_text,
                        "response_time_ms": int(
                            (result.completed_at - result.started_at) * 1000
                        ) if result.completed_at and result.started_at else 0,
                    })

                elif result and result.status == "failed":
                    await websocket.send_json({
                        "type": "error",
                        "message": result.error or "Request failed",
                    })

            else:
                await websocket.send_json({
                    "type": "error",
                    "message": f"Unknown message type: {msg_type}",
                })

    except WebSocketDisconnect:
        log.info("WebSocket disconnected")
    except Exception as e:
        log.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                "type": "error",
                "message": str(e),
            })
        except Exception:
            pass


# ── REST API for queue ────────────────────────────────────────

@ws_router.get("/api/queue/status")
async def queue_status() -> dict:
    """Get request queue status."""
    return _queue.get_status()


@ws_router.post("/api/queue/cancel/{request_id}")
async def cancel_request(request_id: str) -> dict:
    """Cancel a queued request."""
    success = _queue.cancel(request_id)
    return {"cancelled": success, "request_id": request_id}
