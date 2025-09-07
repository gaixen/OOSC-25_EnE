#!/usr/bin/env python3
"""
Test script to verify entity extraction and domain intelligence flow
"""
import asyncio
import os
import sys
sys.path.append('src')

from dotenv import load_dotenv
from orchestrator import EnhancedOrchestrator
from entityExtractor import InfoExtractionAgent

load_dotenv()

async def test_entity_pipeline():
    print("🧪 Testing Entity Extraction Pipeline...")
    
    # Test 1: Basic entity extraction
    entity_extractor = InfoExtractionAgent()
    test_text = "I work at Google and need to discuss our competition with Microsoft and Apple."
    
    print(f"📝 Testing with text: '{test_text}'")
    result = entity_extractor.process_text(test_text)
    print(f"📊 Entity extraction result: {result}")
    
    # Test 2: Orchestrator startup
    print("\n🚀 Testing orchestrator startup...")
    try:
        await EnhancedOrchestrator.start()
        print("✅ Orchestrator started successfully")
    except Exception as e:
        print(f"❌ Orchestrator startup failed: {e}")
        return
    
    # Test 3: Simulate transcript event
    print("\n📤 Simulating transcript event...")
    from event_bus import Event, STREAMS, event_bus
    
    try:
        publish_result = await event_bus.publish(STREAMS['transcripts'], Event(
            type='transcript_received',
            session_id='test_session_123',
            agent_id='voice_transcriber',
            data={'text': test_text}
        ))
        print(f"✅ Published test transcript: {publish_result}")
        
        # Wait a bit for processing
        print("⏳ Waiting for processing...")
        await asyncio.sleep(5)
        
        # Check session context
        if 'test_session_123' in EnhancedOrchestrator.session_contexts:
            context = EnhancedOrchestrator.session_contexts['test_session_123']
            print(f"📊 Session context: {context}")
        else:
            print("❌ No session context found")
            
    except Exception as e:
        print(f"❌ Event publishing failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_entity_pipeline())
