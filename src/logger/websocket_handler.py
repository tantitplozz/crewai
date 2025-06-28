"""
WebSocket Handler for Real-time Updates
"""
import asyncio
import websockets
import json
from typing import Dict, Any, Optional
from datetime import datetime
import aiohttp

class WebSocketHandler:
    """Handle WebSocket connections for real-time updates"""

    def __init__(self, ws_url: str):
        self.ws_url = ws_url
        self.websocket = None
        self.connected = False
        self.reconnect_interval = 5
        self.max_reconnect_attempts = 10
        self.reconnect_attempts = 0
        self.message_queue = asyncio.Queue()
        self.connection_task = None

    async def connect(self):
        """Connect to WebSocket server"""
        self.connection_task = asyncio.create_task(self._maintain_connection())

    async def _maintain_connection(self):
        """Maintain WebSocket connection with auto-reconnect"""
        while self.reconnect_attempts < self.max_reconnect_attempts:
            try:
                # Try websocket connection
                async with websockets.connect(self.ws_url) as websocket:
                    self.websocket = websocket
                    self.connected = True
                    self.reconnect_attempts = 0
                    print(f"WebSocket connected to {self.ws_url}")

                    # Send queued messages
                    asyncio.create_task(self._send_queued_messages())

                    # Keep connection alive
                    while True:
                        try:
                            # Send ping every 30 seconds
                            await asyncio.sleep(30)
                            await websocket.ping()
                        except websockets.ConnectionClosed:
                            break
                        except Exception as e:
                            print(f"WebSocket error: {e}")
                            break

            except Exception as e:
                print(f"WebSocket connection failed: {e}")
                self.connected = False
                self.websocket = None

                # Wait before reconnecting
                self.reconnect_attempts += 1
                if self.reconnect_attempts < self.max_reconnect_attempts:
                    await asyncio.sleep(self.reconnect_interval)
                else:
                    print("Max reconnection attempts reached")
                    break

    async def send_update(self, data: Dict[str, Any]):
        """Send update via WebSocket"""
        message = {
            'timestamp': datetime.now().isoformat(),
            'data': data
        }

        # Add to queue
        await self.message_queue.put(message)

        # Try to send immediately if connected
        if self.connected and self.websocket:
            try:
                await self.websocket.send(json.dumps(message))
            except Exception as e:
                print(f"Failed to send WebSocket message: {e}")
                # Message remains in queue for retry

    async def _send_queued_messages(self):
        """Send messages from queue"""
        while self.connected:
            try:
                # Get message from queue with timeout
                message = await asyncio.wait_for(
                    self.message_queue.get(),
                    timeout=1.0
                )

                if self.websocket:
                    await self.websocket.send(json.dumps(message))

            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Error sending queued message: {e}")
                # Put message back in queue
                await self.message_queue.put(message)
                await asyncio.sleep(1)

    async def send_action_update(self, action: str, details: Dict[str, Any]):
        """Send action update"""
        await self.send_update({
            'type': 'action',
            'action': action,
            'details': details
        })

    async def send_status_update(self, status: str, message: str):
        """Send status update"""
        await self.send_update({
            'type': 'status',
            'status': status,
            'message': message
        })

    async def send_progress_update(self, step: str, progress: int, total: int):
        """Send progress update"""
        await self.send_update({
            'type': 'progress',
            'step': step,
            'progress': progress,
            'total': total,
            'percentage': round((progress / total) * 100, 2)
        })

    async def send_screenshot(self, screenshot_path: str, description: str):
        """Send screenshot notification"""
        await self.send_update({
            'type': 'screenshot',
            'path': screenshot_path,
            'description': description
        })

    async def send_error(self, error: str, details: Optional[Dict[str, Any]] = None):
        """Send error notification"""
        await self.send_update({
            'type': 'error',
            'error': error,
            'details': details or {}
        })

    async def close(self):
        """Close WebSocket connection"""
        self.connected = False

        if self.connection_task:
            self.connection_task.cancel()

        if self.websocket:
            await self.websocket.close()

        print("WebSocket connection closed")


class WebSocketServer:
    """Simple WebSocket server for testing"""

    def __init__(self, host: str = 'localhost', port: int = 8000):
        self.host = host
        self.port = port
        self.clients = set()

    async def handler(self, websocket, path):
        """Handle WebSocket connections"""
        self.clients.add(websocket)
        print(f"Client connected: {websocket.remote_address}")

        try:
            async for message in websocket:
                # Echo message to all clients
                data = json.loads(message)
                print(f"Received: {data}")

                # Broadcast to all connected clients
                disconnected = set()
                for client in self.clients:
                    try:
                        await client.send(message)
                    except websockets.ConnectionClosed:
                        disconnected.add(client)

                # Remove disconnected clients
                self.clients -= disconnected

        except websockets.ConnectionClosed:
            pass
        finally:
            self.clients.remove(websocket)
            print(f"Client disconnected: {websocket.remote_address}")

    async def start(self):
        """Start WebSocket server"""
        print(f"Starting WebSocket server on ws://{self.host}:{self.port}")
        await websockets.serve(self.handler, self.host, self.port)
        await asyncio.Future()  # Run forever


# Alternative HTTP-based update handler for environments without WebSocket
class HTTPUpdateHandler:
    """Send updates via HTTP POST requests"""

    def __init__(self, endpoint_url: str):
        self.endpoint_url = endpoint_url
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def send_update(self, data: Dict[str, Any]):
        """Send update via HTTP POST"""
        if not self.session:
            self.session = aiohttp.ClientSession()

        try:
            async with self.session.post(
                self.endpoint_url,
                json=data,
                timeout=aiohttp.ClientTimeout(total=5)
            ) as response:
                if response.status != 200:
                    print(f"HTTP update failed: {response.status}")
        except Exception as e:
            print(f"Failed to send HTTP update: {e}")
