#!/usr/bin/env python3
"""
Simple test script to verify voice transcription is working
"""
import os
from dotenv import load_dotenv
from src.voice import AssemblyAIRealtimeTranscriber

def test_callback(text):
    print(f"🎯 Test callback received: '{text}'")

def main():
    load_dotenv()
    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    
    if not api_key:
        print("❌ ASSEMBLYAI_API_KEY not found in environment variables")
        return
    
    print("🧪 Testing AssemblyAI transcriber...")
    
    try:
        transcriber = AssemblyAIRealtimeTranscriber(
            api_key=api_key,
            on_transcript_callback=test_callback
        )
        
        print("✅ Transcriber created successfully")
        print("🎤 Starting transcription test...")
        
        transcriber.start_streaming()
        
        print("🗣️ Speak now! Press Enter to stop...")
        input()
        
        transcriber.stop_streaming()
        print("✅ Test completed")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    main()
