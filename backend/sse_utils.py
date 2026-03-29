import json
import queue
import threading
import logging
from datetime import datetime

logger = logging.getLogger("SSE-Utils")

# Thread-safe queue for broadcasting events to all connected clients
sse_subscribers = []
sse_lock = threading.Lock()

def broadcast_sse(event_type: str, data: dict):
    """Push an event to all connected SSE clients."""
    # Add timestamp if not present
    if "timestamp" not in data:
        data["timestamp"] = datetime.now().isoformat()
        
    message = f"event: {event_type}\ndata: {json.dumps(data, default=str)}\n\n"
    
    with sse_lock:
        dead = []
        for i, q in enumerate(sse_subscribers):
            try:
                q.put_nowait(message)
            except (queue.Full, Exception):
                dead.append(i)
        
        # Remove dead subscribers (e.g., closed connections)
        for i in reversed(dead):
            if i < len(sse_subscribers):
                sse_subscribers.pop(i)
                
    if dead:
        logger.debug(f"🧹 Cleaned up {len(dead)} dead SSE connections")
