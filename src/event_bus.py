import asyncio
import json
import redis.asyncio as redis
from typing import Dict, Any, Callable, Optional
from dataclasses import dataclass
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

@dataclass
class Event:
    """Event structure for the message bus"""
    type: str
    session_id: str
    agent_id: str
    data: Dict[str, Any]
    timestamp: float = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().timestamp()

@dataclass 
class ProvenanceEnvelope:
    """Provenance envelope for agent responses"""
    agent_id: str
    timestamp: float
    inputs: Dict[str, Any]
    outputs: Dict[str, Any]
    confidence: float
    sources: list
    processing_time: float = 0.0
    
    def to_dict(self):
        return {
            "agent_id": self.agent_id,
            "timestamp": self.timestamp,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "confidence": self.confidence,
            "sources": self.sources,
            "processing_time": self.processing_time
        }

class EventBus:
    """Redis Streams-based event bus for agent communication"""
    
    def __init__(self, redis_url: str = "redis://localhost:6379"):
        self.redis_url = redis_url
        self.redis_client: Optional[redis.Redis] = None
        self.subscribers: Dict[str, Callable] = {}
        self.running = False
        
    async def connect(self):
        """Connect to Redis"""
        try:
            self.redis_client = redis.from_url(self.redis_url)
            await self.redis_client.ping()
            logger.info("🔌 Connected to Redis event bus")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to connect to Redis: {e}")
            return False
    
    async def publish(self, stream: str, event: Event):
        """Publish event to stream"""
        if not self.redis_client:
            logger.error("❌ Redis client not connected")
            return False
            
        try:
            event_data = {
                "type": event.type,
                "session_id": event.session_id,
                "agent_id": event.agent_id,
                "data": json.dumps(event.data),
                "timestamp": str(event.timestamp)
            }
            
            message_id = await self.redis_client.xadd(stream, event_data)
            logger.debug(f"📤 Published {event.type} to {stream}: {message_id}")
            return message_id
            
        except Exception as e:
            logger.error(f"❌ Failed to publish event: {e}")
            return False
    
    async def subscribe(self, stream: str, consumer_group: str, consumer_name: str, callback: Callable):
        """Subscribe to stream with consumer group"""
        if not self.redis_client:
            logger.error("❌ Redis client not connected") 
            return
            
        try:
            # Create consumer group if it doesn't exist
            try:
                await self.redis_client.xgroup_create(stream, consumer_group, id='0', mkstream=True)
            except redis.RedisError:
                pass  # Group might already exist
            
            logger.info(f"🔊 Subscribed to {stream} as {consumer_name}")
            
            while self.running:
                try:
                    # Read from stream
                    messages = await self.redis_client.xreadgroup(
                        consumer_group, consumer_name, {stream: '>'}, count=1, block=1000
                    )
                    
                    for stream_name, msgs in messages:
                        for msg_id, fields in msgs:
                            try:
                                # Parse event
                                event = Event(
                                    type=fields[b'type'].decode(),
                                    session_id=fields[b'session_id'].decode(),
                                    agent_id=fields[b'agent_id'].decode(),
                                    data=json.loads(fields[b'data'].decode()),
                                    timestamp=float(fields[b'timestamp'].decode())
                                )
                                
                                # Process event
                                await callback(event)
                                
                                # Acknowledge message
                                await self.redis_client.xack(stream, consumer_group, msg_id)
                                
                            except Exception as e:
                                logger.error(f"❌ Error processing message {msg_id}: {e}")
                                
                except redis.ConnectionError:
                    logger.warning("🔄 Redis connection lost, retrying...")
                    await asyncio.sleep(1)
                    
        except Exception as e:
            logger.error(f"❌ Subscription error: {e}")
    
    def start_listening(self):
        """Start listening for events"""
        self.running = True
        
    def stop_listening(self):
        """Stop listening for events"""
        self.running = False
    
    async def close(self):
        """Close Redis connection"""
        if self.redis_client:
            await self.redis_client.close()
            logger.info("🔌 Closed Redis connection")

# Global event bus instance
event_bus = EventBus()

# Stream names
STREAMS = {
    'transcripts': 'meeting:transcripts',
    'entities': 'meeting:entities', 
    'domain_requests': 'meeting:domain_requests',
    'domain_responses': 'meeting:domain_responses',
    'suggestions': 'meeting:suggestions',
    'ui_updates': 'meeting:ui_updates',
    'agent_status': 'meeting:agent_status'
}

async def init_event_bus():
    """Initialize the event bus"""
    return await event_bus.connect()
