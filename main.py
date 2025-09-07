import asyncio
import uuid
import os
import io
import tempfile
import threading
import queue
import uvicorn
from typing import Dict
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, File, UploadFile, Form
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis
import json

from src.voice import AssemblyAIRealtimeTranscriber
from src.event_bus import init_event_bus, event_bus, Event, STREAMS
from src.orchestrator import orchestrator
from src.entityExtractor import InfoExtractionAgent
from src.companyProfileAgent import CompanyProfileAgent
from src.companyNews import CompanyNewsAgent
from src.marketCompetitor import CompetitorMarketAIAgent
from src.personEnrichment import PersonEnrichmentAgent
from src.suggestion_agent import SuggestionGeneratorAgent
from src.ranking_agent import RankingAgent
from src.retriever_agent import RetrieverAgent

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

redis_client = None
active_connections: Dict[str, WebSocket] = {}

@app.on_event("startup")
async def startup():
    global redis_client
    redis_client = redis.from_url("redis://localhost:6379")
    
    # Initialize event bus and orchestrator
    await init_event_bus()
    await orchestrator.start()
    
    # Subscribe to suggestion events for WebSocket forwarding
    asyncio.create_task(event_bus.subscribe(
        STREAMS['suggestions'],
        'ui_group',
        'ui_consumer',
        forward_suggestions_to_websocket
    ))
    
    # Subscribe to agent status events
    asyncio.create_task(event_bus.subscribe(
        STREAMS['agent_status'],
        'ui_group', 
        'status_consumer',
        forward_agent_status_to_websocket
    ))
    
    print("🚀 FastAPI backend started with enhanced orchestration")

@app.on_event("shutdown")
async def shutdown():
    if redis_client:
        await redis_client.close()
    await event_bus.close()

async def forward_suggestions_to_websocket(event: Event):
    """Forward suggestion events to WebSocket connections"""
    session_id = event.session_id
    if session_id in active_connections:
        try:
            message = {
                "type": "suggestions",
                "data": event.data.get('suggestions', []),
                "provenance_chain": event.data.get('provenance_chain', []),
                "current_agent": event.data.get('current_agent', 'unknown')
            }
            await active_connections[session_id].send_text(json.dumps(message))
            print(f"📡 Forwarded suggestions to WebSocket for session: {session_id}")
        except Exception as e:
            print(f"❌ Error forwarding suggestions: {e}")

async def forward_agent_status_to_websocket(event: Event):
    """Forward agent status updates to WebSocket connections"""
    session_id = event.session_id
    print(f"🔍 FORWARD: Checking WebSocket for session {session_id}, active connections: {list(active_connections.keys())}")
    
    if session_id in active_connections:
        try:
            # Build the message data
            message_data = {
                "agent_name": event.data.get('agent_name'),
                "status": event.data.get('status'),
                "timestamp": event.data.get('timestamp')
            }
            
            # Include results data if present (for completed agents)
            if event.data.get('results'):
                message_data['results'] = event.data.get('results')
                print(f"🔍 FORWARD: Including results data for {event.data.get('agent_name')}: {type(event.data.get('results'))}")
            
            message = {
                "type": "agent_status",
                "data": message_data
            }
            
            await active_connections[session_id].send_text(json.dumps(message))
            print(f"📊 FORWARD: Sent agent status to WebSocket: {event.data.get('agent_name')} - {event.data.get('status')}")
        except Exception as e:
            print(f"❌ FORWARD: Error sending agent status to WebSocket: {e}")
            # Clean up dead connection
            if session_id in active_connections:
                del active_connections[session_id]
    else:
        print(f"❌ FORWARD: No WebSocket connection found for session: {session_id}")

class MeetingProcessor:
    """Simplified meeting processor that publishes to event bus"""
    def __init__(self):
        self.transcribers = {}
        self.transcript_queues = {}
        self.queue_processors = {}

    def create_transcriber(self, session_id: str):
        print(f"🔧 Creating transcriber for session: {session_id}")
        self.transcript_queues[session_id] = queue.Queue()
        
        def on_transcript(text: str):
            print(f"📝 Transcript callback received: '{text}' for session: {session_id}")
            self.transcript_queues[session_id].put(text)
        
        transcriber = AssemblyAIRealtimeTranscriber(
            api_key=os.getenv("ASSEMBLYAI_API_KEY"),
            on_transcript_callback=on_transcript
        )
        self.transcribers[session_id] = transcriber
        print(f"✅ Transcriber created successfully for session: {session_id}")
        return transcriber

    async def start_queue_processor(self, session_id: str):
        """Start processing transcripts from the queue for this session"""
        print(f"🔄 Starting queue processor for session: {session_id}")
        while session_id in self.transcript_queues:
            try:
                text = self.transcript_queues[session_id].get_nowait()
                print(f"📤 Processing transcript from queue: '{text}'")
                await self.handle_transcript(session_id, text)
            except queue.Empty:
                await asyncio.sleep(0.1)
            except Exception as e:
                print(f"❌ Error processing transcript queue: {e}")
                break

    async def handle_transcript(self, session_id: str, text: str):
        """Handle transcript by sending to frontend and event bus"""
        print(f"🎯 Handling transcript for session {session_id}: '{text}'")
        
        # Send to frontend immediately for live captions
        if session_id in active_connections:
            try:
                message = {
                    "type": "transcription",
                    "data": {"text": text}
                }
                print(f"📡 Sending transcript to frontend: {message}")
                await active_connections[session_id].send_text(json.dumps(message))
            except Exception as ws_send_error:
                print(f"⚠️ Failed to send transcript via WebSocket: {ws_send_error}")
        else:
            print(f"❌ No active connection for session: {session_id}")
        
        # Publish to event bus for orchestrator processing
        print(f"📤 MAIN: Publishing transcript to event bus: '{text}'")
        try:
            publish_result = await event_bus.publish(STREAMS['transcripts'], Event(
                type='transcript_received',
                session_id=session_id,
                agent_id='voice_transcriber',
                data={'text': text}
            ))
            print(f"✅ MAIN: Published transcript to event bus: {publish_result}")
        except Exception as e:
            print(f"❌ MAIN: Failed to publish transcript to event bus: {e}")
            # Don't crash - continue processing even if event bus fails

    def start_voice_streaming(self, session_id: str):
        print(f"🎤 Starting voice streaming for session: {session_id}")
        if session_id not in self.transcribers:
            transcriber = self.create_transcriber(session_id)
            transcriber.start_streaming()
            # Start the queue processor for this session
            asyncio.create_task(self.start_queue_processor(session_id))
        else:
            print(f"⚠️ Transcriber already exists for session: {session_id}")
            self.transcribers[session_id].start_streaming()

    def stop_voice_streaming(self, session_id: str):
        print(f"🛑 Stopping voice streaming for session: {session_id}")
        try:
            if session_id in self.transcribers:
                transcriber = self.transcribers[session_id]
                try:
                    transcriber.stop_streaming()
                    print(f"🔇 Transcriber stopped for session: {session_id}")
                except Exception as transcriber_error:
                    print(f"⚠️ Error stopping transcriber: {transcriber_error}")
                finally:
                    # Always remove from dict even if stop failed
                    del self.transcribers[session_id]
                    print(f"🗑️ Transcriber removed from session: {session_id}")
                
            if session_id in self.transcript_queues:
                try:
                    del self.transcript_queues[session_id]
                    print(f"🗑️ Transcript queue removed for session: {session_id}")
                except Exception as queue_error:
                    print(f"⚠️ Error removing transcript queue: {queue_error}")
                
            print(f"✅ Voice streaming stopped successfully for session: {session_id}")
            
        except Exception as e:
            print(f"❌ Error stopping voice streaming for session {session_id}: {e}")
            # Force cleanup even if there's an error - but don't crash the backend
            try:
                if session_id in self.transcribers:
                    del self.transcribers[session_id]
                    print(f"🔧 Force-removed transcriber for session: {session_id}")
            except:
                print(f"⚠️ Could not force-remove transcriber for session: {session_id}")
                
            try:
                if session_id in self.transcript_queues:
                    del self.transcript_queues[session_id]
                    print(f"🔧 Force-removed transcript queue for session: {session_id}")
            except:
                print(f"⚠️ Could not force-remove transcript queue for session: {session_id}")
            
            print(f"🛡️ Backend remains stable despite voice streaming errors for session: {session_id}")

    # Legacy methods kept for backward compatibility
    async def process_utterance(self, session_id: str, text: str):
        """Legacy method - now just publishes to event bus"""
        await self.handle_transcript(session_id, text)

processor = MeetingProcessor()

@app.post("/api/start-meeting")
async def start_meeting():
    session_id = str(uuid.uuid4())
    return {"session_id": session_id}

@app.post("/api/process-audio")
async def process_audio(audio: UploadFile = File(...), session_id: str = Form(...)):
    try:
        audio_data = await audio.read()
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmp_file:
            tmp_file.write(audio_data)
            tmp_file_path = tmp_file.name
        
        try:
            result = processor.whisper_model.transcribe(tmp_file_path)
            text = result["text"].strip()
            
            if text:
                if session_id in active_connections:
                    await active_connections[session_id].send_text(json.dumps({
                        "type": "transcription",
                        "data": {"text": text}
                    }))
                
                await processor.process_utterance(session_id, text)
            
            return {"transcription": text, "status": "processed"}
        finally:
            os.unlink(tmp_file_path)
            
    except Exception as e:
        return {"error": str(e), "transcription": ""}

@app.post("/api/voice-control")
async def voice_control(data: dict):
    session_id = data["session_id"]
    action = data["action"]
    print(f"🎛️ Voice control request: {action} for session: {session_id}")
    
    try:
        if action == "start":
            processor.start_voice_streaming(session_id)
        elif action == "stop":
            processor.stop_voice_streaming(session_id)
        
        return {"status": "success", "action": action, "session_id": session_id}
    except Exception as e:
        print(f"❌ Voice control error: {e}")
        return {"status": "error", "message": str(e)}

@app.post("/api/process-utterance")
async def process_utterance(data: dict):
    session_id = data["session_id"]
    text = data["text"]
    await processor.process_utterance(session_id, text)
    return {"status": "processed"}

@app.websocket("/ws/{session_id}")
async def websocket_endpoint(websocket: WebSocket, session_id: str):
    await websocket.accept()
    active_connections[session_id] = websocket
    print(f"🔌 WebSocket connected for session: {session_id}")
    
    try:
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                print(f"📨 WebSocket message received: {message}")
                
                if message["type"] == "utterance":
                    await processor.process_utterance(session_id, message["text"])
                elif message["type"] == "start_voice":
                    processor.start_voice_streaming(session_id)
                elif message["type"] == "stop_voice":
                    processor.stop_voice_streaming(session_id)
                    
            except json.JSONDecodeError as json_error:
                print(f"⚠️ Invalid JSON received on WebSocket: {json_error}")
                await websocket.send_text(json.dumps({
                    "type": "error", 
                    "message": "Invalid JSON format"
                }))
            except KeyError as key_error:
                print(f"⚠️ Missing required field in WebSocket message: {key_error}")
                await websocket.send_text(json.dumps({
                    "type": "error", 
                    "message": f"Missing required field: {key_error}"
                }))
            except Exception as msg_error:
                print(f"⚠️ Error processing WebSocket message: {msg_error}")
                await websocket.send_text(json.dumps({
                    "type": "error", 
                    "message": "Error processing message"
                }))
                
    except WebSocketDisconnect:
        print(f"🔌 WebSocket disconnected for session: {session_id}")
    except Exception as ws_error:
        print(f"❌ Unexpected WebSocket error for session {session_id}: {ws_error}")
    finally:
        # Always clean up when WebSocket closes
        print(f"🧹 Cleaning up WebSocket resources for session: {session_id}")
        try:
            processor.stop_voice_streaming(session_id)
        except Exception as cleanup_error:
            print(f"⚠️ Error during voice cleanup: {cleanup_error}")
        
        if session_id in active_connections:
            try:
                del active_connections[session_id]
                print(f"🗑️ Removed WebSocket connection for session: {session_id}")
            except Exception as conn_error:
                print(f"⚠️ Error removing connection: {conn_error}")
                
        print(f"✅ WebSocket cleanup completed for session: {session_id}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
