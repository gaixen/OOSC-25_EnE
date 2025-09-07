#!/usr/bin/env python3
"""
Test script to verify voice transcription fixes for segmentation fault issue
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.voice import AssemblyAIRealtimeTranscriber

def test_transcriber():
    """Test transcriber initialization and cleanup without segfaults"""
    print("🧪 Testing voice transcriber fixes...")
    
    try:
        # Test with fake API key (should not crash)
        transcriber = AssemblyAIRealtimeTranscriber(
            api_key="test_key",
            on_transcript_callback=lambda text: print(f"Transcript: {text}")
        )
        
        print("✅ Transcriber initialized successfully")
        
        # Test cleanup without starting (should not crash)
        transcriber.cleanup()
        print("✅ Cleanup completed without crash")
        
        # Test multiple cleanup calls (should not crash)
        transcriber.cleanup()
        transcriber.cleanup()
        print("✅ Multiple cleanup calls handled gracefully")
        
        print("🎉 All tests passed! Voice fixes should prevent segmentation faults.")
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_transcriber()
    sys.exit(0 if success else 1)
