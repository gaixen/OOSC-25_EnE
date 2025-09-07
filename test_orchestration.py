#!/usr/bin/env python3
"""
Test script for the enhanced orchestration system
"""
import asyncio
import os
from src.event_bus import Event, STREAMS, event_bus

async def test_event_bus():
    """Test the event bus functionality"""
    print("🧪 Testing Enhanced Orchestration System")
    
    # Connect to event bus
    connected = await event_bus.connect()
    if not connected:
        print("❌ Failed to connect to Redis. Make sure Redis is running.")
        return
    
    print("✅ Connected to Redis event bus")
    
    # Test publishing an event
    test_event = Event(
        type='test_transcript',
        session_id='test_session_123',
        agent_id='test_agent',
        data={'text': 'Hello, this is a test transcript from Microsoft.'}
    )
    
    print("📤 Publishing test transcript event...")
    result = await event_bus.publish(STREAMS['transcripts'], test_event)
    
    if result:
        print(f"✅ Event published successfully: {result}")
    else:
        print("❌ Failed to publish event")
    
    # Give some time for orchestrator to process
    print("⏳ Waiting 5 seconds for orchestrator to process...")
    await asyncio.sleep(5)
    
    await event_bus.close()
    print("🏁 Test completed")

if __name__ == "__main__":
    asyncio.run(test_event_bus())
