"""
WebSocket Mock Framework

Comprehensive mocking infrastructure for WebSocket communications used in 
state_broadcaster.py (125 lines) and real-time state visualization.

Provides realistic simulation of:
- WebSocket server operations
- Client connection management
- Message broadcasting and unicasting
- Connection lifecycle events
- Error conditions and reconnection
- Real-time state synchronization

Designed for government audit compliance with 95%+ test coverage requirements.
"""

import asyncio
import json
import logging
import random
import time
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set, Any, Callable, Union
from unittest.mock import AsyncMock, Mock, MagicMock
from enum import Enum
import weakref

logger = logging.getLogger(__name__)


class MockWebSocketState(Enum):
    """Mock WebSocket connection states"""
    CONNECTING = 0
    OPEN = 1
    CLOSING = 2
    CLOSED = 3


class MockWebSocketCloseCode(Enum):
    """Mock WebSocket close codes"""
    NORMAL_CLOSURE = 1000
    GOING_AWAY = 1001
    PROTOCOL_ERROR = 1002
    UNSUPPORTED_DATA = 1003
    INVALID_FRAME_PAYLOAD_DATA = 1007
    POLICY_VIOLATION = 1008
    MESSAGE_TOO_BIG = 1009
    MANDATORY_EXTENSION = 1010
    INTERNAL_ERROR = 1011


class MockWebSocketMessage:
    """Mock WebSocket message with realistic behavior"""
    
    def __init__(self, data: Union[str, bytes], message_type: str = "text"):
        self.data = data
        self.type = message_type
        self.timestamp = datetime.now(timezone.utc)
        self.size = len(data) if isinstance(data, (str, bytes)) else 0
        
    def __str__(self):
        return f"MockWebSocketMessage({self.type}, {self.size} bytes)"
        
    def to_dict(self):
        """Convert message to dictionary for serialization"""
        return {
            'data': self.data,
            'type': self.type,
            'timestamp': self.timestamp.isoformat(),
            'size': self.size
        }


class MockWebSocketConnection:
    """
    Mock WebSocket connection with realistic behavior simulation.
    
    Simulates individual client connections including:
    - Connection state management
    - Message queuing and delivery
    - Ping/pong handling
    - Error simulation
    - Bandwidth simulation
    """
    
    def __init__(self, connection_id: str = None, remote_address: str = None):
        self.id = connection_id or f"conn_{random.randint(100000, 999999)}"
        self.remote_address = remote_address or f"127.0.0.1:{random.randint(50000, 65000)}"
        self.state = MockWebSocketState.CONNECTING
        self.close_code = None
        self.close_reason = None
        self.connected_at = datetime.now(timezone.utc)
        self.closed_at = None
        self.last_ping = None
        self.last_pong = None
        
        # Message handling
        self._message_queue = asyncio.Queue()
        self._sent_messages = []
        self._received_messages = []
        self._message_handlers = {}
        
        # Connection settings
        self.max_message_size = 64 * 1024  # 64KB default
        self.ping_interval = 30.0
        self.ping_timeout = 10.0
        self.compression = None
        
        # Mock behavior settings
        self.failure_rate = 0.02  # 2% message failure rate
        self.latency_range = (0.01, 0.1)  # 10-100ms latency
        self.bandwidth_limit = None  # No limit by default
        
        # Event callbacks
        self.on_open = AsyncMock()
        self.on_message = AsyncMock()
        self.on_close = AsyncMock()
        self.on_error = AsyncMock()
        
    async def open(self):
        """Simulate connection opening"""
        await asyncio.sleep(random.uniform(0.05, 0.2))  # Connection delay
        self.state = MockWebSocketState.OPEN
        self.connected_at = datetime.now(timezone.utc)
        await self.on_open(self)
        logger.debug(f"Mock WebSocket connection {self.id} opened")
        
    async def close(self, code: int = 1000, reason: str = ""):
        """Simulate connection closing"""
        if self.state == MockWebSocketState.CLOSED:
            return
            
        self.state = MockWebSocketState.CLOSING
        self.close_code = code
        self.close_reason = reason
        
        await asyncio.sleep(random.uniform(0.01, 0.05))  # Closing delay
        
        self.state = MockWebSocketState.CLOSED
        self.closed_at = datetime.now(timezone.utc)
        await self.on_close(self, code, reason)
        logger.debug(f"Mock WebSocket connection {self.id} closed with code {code}")
        
    async def send(self, data: Union[str, bytes, Dict]):
        """Send data through the WebSocket connection"""
        if self.state != MockWebSocketState.OPEN:
            raise ConnectionError(f"Connection {self.id} is not open")
            
        # Convert dict to JSON string
        if isinstance(data, dict):
            data = json.dumps(data)
            
        message = MockWebSocketMessage(data)
        
        # Simulate message size limit
        if message.size > self.max_message_size:
            raise ValueError(f"Message size {message.size} exceeds limit {self.max_message_size}")
            
        # Simulate network latency
        latency = random.uniform(*self.latency_range)
        await asyncio.sleep(latency)
        
        # Simulate occasional failures
        if random.random() < self.failure_rate:
            error = ConnectionError(f"Simulated network error on connection {self.id}")
            await self.on_error(error)
            raise error
            
        self._sent_messages.append(message)
        logger.debug(f"Mock WebSocket {self.id} sent message: {message}")
        
    async def receive(self, timeout: float = None):
        """Receive data from the WebSocket connection"""
        if self.state != MockWebSocketState.OPEN:
            raise ConnectionError(f"Connection {self.id} is not open")
            
        try:
            if timeout:
                message = await asyncio.wait_for(self._message_queue.get(), timeout=timeout)
            else:
                message = await self._message_queue.get()
                
            self._received_messages.append(message)
            await self.on_message(message)
            return message.data
            
        except asyncio.TimeoutError:
            raise TimeoutError(f"Receive timeout on connection {self.id}")
            
    async def ping(self, data: bytes = b""):
        """Send ping frame"""
        if self.state != MockWebSocketState.OPEN:
            return False
            
        self.last_ping = datetime.now(timezone.utc)
        
        # Simulate ping delay
        await asyncio.sleep(random.uniform(0.001, 0.01))
        
        # Auto-respond with pong
        await self.pong(data)
        return True
        
    async def pong(self, data: bytes = b""):
        """Send pong frame"""
        if self.state != MockWebSocketState.OPEN:
            return False
            
        self.last_pong = datetime.now(timezone.utc)
        logger.debug(f"Mock WebSocket {self.id} pong sent")
        return True
        
    def add_message_handler(self, message_type: str, handler: Callable):
        """Add message handler for specific message types"""
        self._message_handlers[message_type] = handler
        
    async def simulate_incoming_message(self, data: Union[str, bytes, Dict]):
        """Simulate receiving a message (for testing)"""
        if isinstance(data, dict):
            data = json.dumps(data)
            
        message = MockWebSocketMessage(data)
        await self._message_queue.put(message)
        logger.debug(f"Mock WebSocket {self.id} queued incoming message: {message}")
        
    def get_sent_messages(self) -> List[MockWebSocketMessage]:
        """Get list of sent messages for testing"""
        return self._sent_messages.copy()
        
    def get_received_messages(self) -> List[MockWebSocketMessage]:
        """Get list of received messages for testing"""
        return self._received_messages.copy()
        
    def get_connection_stats(self) -> Dict:
        """Get connection statistics for testing"""
        duration = None
        if self.connected_at:
            end_time = self.closed_at or datetime.now(timezone.utc)
            duration = (end_time - self.connected_at).total_seconds()
            
        return {
            'id': self.id,
            'state': self.state.name,
            'remote_address': self.remote_address,
            'connected_at': self.connected_at.isoformat() if self.connected_at else None,
            'closed_at': self.closed_at.isoformat() if self.closed_at else None,
            'duration': duration,
            'messages_sent': len(self._sent_messages),
            'messages_received': len(self._received_messages),
            'close_code': self.close_code,
            'close_reason': self.close_reason
        }


class MockWebSocketServer:
    """
    Comprehensive WebSocket server mock with realistic behavior simulation.
    
    Provides full simulation of WebSocket server functionality including:
    - Client connection management
    - Message broadcasting
    - Connection lifecycle events
    - Load balancing simulation
    - Performance monitoring
    """
    
    def __init__(self, host: str = "localhost", port: int = 8765):
        self.host = host
        self.port = port
        self.is_serving = False
        self.started_at = None
        self.stopped_at = None
        
        # Connection management
        self._connections: Dict[str, MockWebSocketConnection] = {}
        self._connection_handlers = []
        self._message_handlers = {}
        
        # Server settings
        self.max_connections = 1000
        self.max_message_size = 64 * 1024
        self.ping_interval = 30.0
        self.ping_timeout = 10.0
        
        # Statistics
        self._total_connections = 0
        self._total_messages = 0
        self._broadcasts_sent = 0
        
        # Event callbacks
        self.on_connection = AsyncMock()
        self.on_disconnection = AsyncMock()
        self.on_message = AsyncMock()
        self.on_broadcast = AsyncMock()
        
    async def start(self):
        """Start the mock WebSocket server"""
        if self.is_serving:
            return
            
        await asyncio.sleep(random.uniform(0.1, 0.3))  # Startup delay
        self.is_serving = True
        self.started_at = datetime.now(timezone.utc)
        logger.info(f"Mock WebSocket server started on {self.host}:{self.port}")
        
    async def stop(self):
        """Stop the mock WebSocket server"""
        if not self.is_serving:
            return
            
        # Close all connections
        close_tasks = []
        for connection in self._connections.values():
            close_tasks.append(connection.close(1001, "Server shutdown"))
            
        if close_tasks:
            await asyncio.gather(*close_tasks, return_exceptions=True)
            
        self.is_serving = False
        self.stopped_at = datetime.now(timezone.utc)
        self._connections.clear()
        logger.info(f"Mock WebSocket server stopped")
        
    async def add_connection(self, connection_id: str = None, 
                           remote_address: str = None) -> MockWebSocketConnection:
        """Add a new connection to the server"""
        if not self.is_serving:
            raise RuntimeError("Server is not running")
            
        if len(self._connections) >= self.max_connections:
            raise ConnectionError("Maximum connections reached")
            
        connection = MockWebSocketConnection(connection_id, remote_address)
        self._connections[connection.id] = connection
        self._total_connections += 1
        
        await connection.open()
        await self.on_connection(connection)
        
        logger.debug(f"Mock WebSocket server added connection {connection.id}")
        return connection
        
    async def remove_connection(self, connection_id: str, 
                              code: int = 1000, reason: str = ""):
        """Remove a connection from the server"""
        if connection_id not in self._connections:
            return
            
        connection = self._connections[connection_id]
        await connection.close(code, reason)
        
        del self._connections[connection_id]
        await self.on_disconnection(connection, code, reason)
        
        logger.debug(f"Mock WebSocket server removed connection {connection_id}")
        
    async def broadcast(self, data: Union[str, bytes, Dict], 
                       exclude: Set[str] = None):
        """Broadcast data to all connected clients"""
        if not self.is_serving:
            raise RuntimeError("Server is not running")
            
        exclude = exclude or set()
        broadcast_tasks = []
        
        for connection in self._connections.values():
            if connection.id not in exclude and connection.state == MockWebSocketState.OPEN:
                broadcast_tasks.append(connection.send(data))
                
        if broadcast_tasks:
            results = await asyncio.gather(*broadcast_tasks, return_exceptions=True)
            success_count = sum(1 for r in results if not isinstance(r, Exception))
            
            self._broadcasts_sent += 1
            await self.on_broadcast(data, success_count, len(broadcast_tasks))
            
            logger.debug(f"Mock WebSocket server broadcast to {success_count}/{len(broadcast_tasks)} connections")
            return success_count
        else:
            return 0
            
    async def send_to_connection(self, connection_id: str, 
                               data: Union[str, bytes, Dict]):
        """Send data to a specific connection"""
        if connection_id not in self._connections:
            raise KeyError(f"Connection {connection_id} not found")
            
        connection = self._connections[connection_id]
        await connection.send(data)
        self._total_messages += 1
        
    def get_connection(self, connection_id: str) -> Optional[MockWebSocketConnection]:
        """Get connection by ID"""
        return self._connections.get(connection_id)
        
    def get_connections(self) -> List[MockWebSocketConnection]:
        """Get all active connections"""
        return list(self._connections.values())
        
    def get_connection_count(self) -> int:
        """Get current connection count"""
        return len(self._connections)
        
    def get_server_stats(self) -> Dict:
        """Get server statistics for testing"""
        uptime = None
        if self.started_at:
            end_time = self.stopped_at or datetime.now(timezone.utc)
            uptime = (end_time - self.started_at).total_seconds()
            
        return {
            'host': self.host,
            'port': self.port,
            'is_serving': self.is_serving,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'stopped_at': self.stopped_at.isoformat() if self.stopped_at else None,
            'uptime': uptime,
            'active_connections': len(self._connections),
            'total_connections': self._total_connections,
            'total_messages': self._total_messages,
            'broadcasts_sent': self._broadcasts_sent,
            'max_connections': self.max_connections
        }
        
    def add_message_handler(self, message_type: str, handler: Callable):
        """Add message handler for specific message types"""
        self._message_handlers[message_type] = handler
        
    async def simulate_client_connection(self, connection_id: str = None) -> MockWebSocketConnection:
        """Simulate a client connecting (for testing)"""
        return await self.add_connection(connection_id)
        
    async def simulate_client_message(self, connection_id: str, 
                                    data: Union[str, bytes, Dict]):
        """Simulate a client sending a message (for testing)"""
        if connection_id not in self._connections:
            raise KeyError(f"Connection {connection_id} not found")
            
        connection = self._connections[connection_id]
        await connection.simulate_incoming_message(data)
        await self.on_message(connection, data)
        self._total_messages += 1


class MockWebSocketClient:
    """
    Mock WebSocket client for testing client-side functionality.
    
    Simulates client connections to WebSocket servers including:
    - Connection establishment
    - Message sending and receiving
    - Reconnection logic
    - Error handling
    """
    
    def __init__(self, uri: str):
        self.uri = uri
        self.connection = None
        self.is_connected = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.reconnect_delay = 1.0
        
        # Event callbacks
        self.on_open = AsyncMock()
        self.on_message = AsyncMock()
        self.on_close = AsyncMock()
        self.on_error = AsyncMock()
        
    async def connect(self):
        """Connect to the WebSocket server"""
        if self.is_connected:
            return
            
        # Simulate connection process
        await asyncio.sleep(random.uniform(0.1, 0.5))
        
        # Simulate occasional connection failures
        if random.random() < 0.05:  # 5% failure rate
            error = ConnectionError(f"Failed to connect to {self.uri}")
            await self.on_error(error)
            raise error
            
        self.connection = MockWebSocketConnection()
        await self.connection.open()
        self.is_connected = True
        self.reconnect_attempts = 0
        
        await self.on_open()
        logger.debug(f"Mock WebSocket client connected to {self.uri}")
        
    async def disconnect(self, code: int = 1000, reason: str = ""):
        """Disconnect from the WebSocket server"""
        if not self.is_connected:
            return
            
        if self.connection:
            await self.connection.close(code, reason)
            
        self.is_connected = False
        await self.on_close(code, reason)
        logger.debug(f"Mock WebSocket client disconnected from {self.uri}")
        
    async def send(self, data: Union[str, bytes, Dict]):
        """Send data to the server"""
        if not self.is_connected or not self.connection:
            raise ConnectionError("Client is not connected")
            
        await self.connection.send(data)
        
    async def receive(self, timeout: float = None):
        """Receive data from the server"""
        if not self.is_connected or not self.connection:
            raise ConnectionError("Client is not connected")
            
        return await self.connection.receive(timeout)
        
    async def reconnect(self):
        """Attempt to reconnect to the server"""
        if self.reconnect_attempts >= self.max_reconnect_attempts:
            raise ConnectionError("Maximum reconnection attempts exceeded")
            
        self.reconnect_attempts += 1
        await asyncio.sleep(self.reconnect_delay * self.reconnect_attempts)
        
        try:
            await self.connect()
        except Exception as e:
            await self.on_error(e)
            raise


def create_mock_websocket_server(host: str = "localhost", 
                                port: int = 8765) -> MockWebSocketServer:
    """Factory function to create a mock WebSocket server"""
    return MockWebSocketServer(host, port)


def create_mock_websocket_client(uri: str) -> MockWebSocketClient:
    """Factory function to create a mock WebSocket client"""
    return MockWebSocketClient(uri)


# Export main classes for easy importing
__all__ = [
    'MockWebSocketServer',
    'MockWebSocketClient',
    'MockWebSocketConnection',
    'MockWebSocketMessage',
    'MockWebSocketState',
    'MockWebSocketCloseCode',
    'create_mock_websocket_server',
    'create_mock_websocket_client'
]