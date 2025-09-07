import os
import json
import threading
import time
import wave
from urllib.parse import urlencode
from datetime import datetime
try:
    import pyaudio
    PYAUDIO_AVAILABLE = True
except ImportError:
    PYAUDIO_AVAILABLE = False
    print("Warning: PyAudio not available. Voice functionality will be limited.")
import websocket
from dotenv import load_dotenv


class AssemblyAIRealtimeTranscriber:
    def __init__(self, api_key: str, sample_rate: int = 16000, frames_per_buffer: int = 800, on_transcript_callback=None):
        if not PYAUDIO_AVAILABLE:
            raise RuntimeError("PyAudio is not available. Cannot initialize transcriber.")
            
        self.api_key = api_key
        self.sample_rate = sample_rate
        self.frames_per_buffer = frames_per_buffer
        self.channels = 1
        self.format = pyaudio.paInt16
        self.on_transcript_callback = on_transcript_callback

        connection_params = {"sample_rate": self.sample_rate, "format_turns": True}
        base_url = "wss://streaming.assemblyai.com/v3/ws"
        self.api_endpoint = f"{base_url}?{urlencode(connection_params)}"

        self.audio = None
        self.stream = None
        self.ws_app = None
        self.audio_thread = None
        self.stop_event = threading.Event()
        self.recorded_frames = []
        self.recording_lock = threading.Lock()
        self.cleanup_lock = threading.Lock()
        self.is_running = False
        self.is_cleaning_up = False
        
        print(f"🎤 AssemblyAI Transcriber initialized with callback: {self.on_transcript_callback is not None}")

    # ---------------- Event Handlers ---------------- #
    def on_open(self, ws):
        def stream_audio():
            print("🎵 Audio streaming thread started")
            while not self.stop_event.is_set():
                try:
                    # Check if we still have valid stream and websocket
                    if not self.stream or not ws or self.stop_event.is_set():
                        print("🛑 Stream or WebSocket no longer available, stopping audio thread")
                        break
                        
                    if self.stream.is_active():
                        audio_data = self.stream.read(
                            self.frames_per_buffer, exception_on_overflow=False
                        )
                        
                        # Check again if we should stop before processing data
                        if self.stop_event.is_set():
                            break
                            
                        with self.recording_lock:
                            if not self.stop_event.is_set():  # Double-check before adding frames
                                self.recorded_frames.append(audio_data)
                        
                        # Only send if WebSocket is still connected
                        if ws and not self.stop_event.is_set():
                            ws.send(audio_data, websocket.ABNF.OPCODE_BINARY)
                    else:
                        # Stream not active, break the loop
                        print("🔇 Audio stream no longer active")
                        break
                except Exception as e:
                    print(f"⚠️ Error in audio streaming: {e}")
                    if "stream" in str(e).lower() or "closed" in str(e).lower():
                        print("🛑 Stream-related error, stopping audio thread")
                        break
                    # For non-critical errors, continue but add a small delay
                    time.sleep(0.01)
            print("🎵 Audio streaming thread stopped")

        self.audio_thread = threading.Thread(target=stream_audio, daemon=True)
        self.audio_thread.start()
        print("📡 AssemblyAI WebSocket connection opened")

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            msg_type = data.get("type")
            print(f"🔄 WebSocket message received: {msg_type}")

            if msg_type == "Begin":
                session_id = data.get("id")
                expires_at = data.get("expires_at")
                print(f"📡 AssemblyAI session started: {session_id}")

            elif msg_type == "Turn":
                transcript = data.get("transcript", "")
                formatted = data.get("turn_is_formatted", False)
                print(f"📝 Transcript received: '{transcript}' (formatted: {formatted})")

                if formatted and transcript.strip():
                    print(f"✅ Calling callback with transcript: '{transcript.strip()}'")
                    if self.on_transcript_callback:
                        self.on_transcript_callback(transcript.strip())
                    else:
                        print("❌ No callback function available!")

            elif msg_type == "Termination":
                print("🔚 AssemblyAI session terminated")

        except Exception as e:
            print(f"❌ Error processing message: {e}")

    def on_error(self, ws, error):
        print(f"⚠️ AssemblyAI WebSocket error: {error}")
        # Don't immediately stop - let the system handle this gracefully
        # Only set stop event if this is a critical error that requires shutdown
        if "authentication" in str(error).lower() or "unauthorized" in str(error).lower():
            print("❌ Authentication error - stopping transcription")
            self.stop_event.set()
        else:
            print("🔄 Non-critical error - continuing transcription")

    def on_close(self, ws, code, msg):
        print(f"🔌 AssemblyAI WebSocket closed: code={code}, msg={msg}")
        # Only cleanup if this was an unexpected closure or we're already stopping
        if self.stop_event.is_set() or (code and code not in [1000, 1001]):  # 1000=normal, 1001=going away
            print("🧹 Cleaning up due to unexpected closure or stop event")
            self.cleanup()
        else:
            print("✅ Normal WebSocket closure - no cleanup needed")

    # ---------------- Core Methods ---------------- #
    def start_streaming(self):
        if self.is_running:
            print("⚠️ Transcriber already running")
            return
        
        print("🚀 Starting voice transcription...")
        self.stop_event.clear()
        self.is_running = True
        
        try:
            self.audio = pyaudio.PyAudio()
            print(f"🎤 PyAudio initialized")
        except Exception as e:
            print(f"❌ PyAudio initialization failed: {e}")
            self.cleanup()
            return

        try:
            self.stream = self.audio.open(
                input=True,
                frames_per_buffer=self.frames_per_buffer,
                channels=self.channels,
                format=self.format,
                rate=self.sample_rate,
            )
            print(f"🔊 Audio stream opened successfully")
        except Exception as e:
            print(f"❌ Audio stream failed: {e}")
            self.cleanup()
            return

        self.ws_app = websocket.WebSocketApp(
            self.api_endpoint,
            header={"Authorization": self.api_key},
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
        )
        print(f"🌐 WebSocket connection starting...")

        ws_thread = threading.Thread(target=self.ws_app.run_forever, daemon=True)
        ws_thread.start()
        print(f"✅ Voice transcription started successfully")

    def stop_streaming(self):
        if not self.is_running:
            print("⚠️ Transcriber already stopped")
            return
            
        print("🛑 Stopping voice transcription...")
        self.is_running = False
        self.stop_event.set()
        
        try:
            # Gracefully close WebSocket first
            if self.ws_app and self.ws_app.sock and self.ws_app.sock.connected:
                try:
                    self.ws_app.send(json.dumps({"type": "Terminate"}))
                    print("📡 Sent termination signal to AssemblyAI")
                    time.sleep(0.2)  # Give time for graceful shutdown
                except Exception as e:
                    print(f"⚠️ Error sending termination signal: {e}")
                    
            if self.ws_app:
                try:
                    self.ws_app.close()
                    print("🌐 WebSocket connection closed")
                except Exception as e:
                    print(f"⚠️ Error closing WebSocket: {e}")
                    
        except Exception as e:
            print(f"⚠️ Error during WebSocket cleanup: {e}")
        
        # Wait for audio thread to finish first (before cleanup)
        if self.audio_thread and self.audio_thread.is_alive():
            try:
                self.audio_thread.join(timeout=2.0)
                if self.audio_thread.is_alive():
                    print("⚠️ Audio thread did not terminate gracefully")
                else:
                    print("🧵 Audio thread finished gracefully")
            except Exception as e:
                print(f"⚠️ Error joining audio thread: {e}")
        
        # Clean up audio resources (this will be prevented from running twice by the lock)
        self.cleanup()
        print("✅ Voice transcription stopped successfully")

    def save_wav_file(self):
        """Save recorded audio to a WAV file"""
        if not self.recorded_frames:
            print("⚠️ No audio recorded.")
            return

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"recorded_audio_{timestamp}.wav"

        try:
            with wave.open(filename, "wb") as wf:
                wf.setnchannels(self.channels)
                wf.setsampwidth(2)
                wf.setframerate(self.sample_rate)
                with self.recording_lock:
                    wf.writeframes(b"".join(self.recorded_frames))

            print(f"💾 Audio saved: {filename}")
            duration = len(self.recorded_frames) * self.frames_per_buffer / self.sample_rate
            print(f"   Duration: {duration:.2f} seconds")
        except Exception as e:
            print(f"❌ Error saving WAV: {e}")

    def cleanup(self):
        # Prevent multiple cleanup calls with a lock
        with self.cleanup_lock:
            if self.is_cleaning_up:
                print("🔄 Cleanup already in progress, skipping...")
                return
            
            self.is_cleaning_up = True
            print("🧹 Cleaning up audio resources...")
            self.stop_event.set()
            
            # Close audio stream first
            if self.stream:
                try:
                    if self.stream.is_active():
                        self.stream.stop_stream()
                        print("🔇 Audio stream stopped")
                    self.stream.close()
                    print("🔒 Audio stream closed")
                    self.stream = None
                except Exception as e:
                    print(f"⚠️ Error closing audio stream: {e}")
                    self.stream = None
            
            # Terminate PyAudio
            if self.audio:
                try:
                    self.audio.terminate()
                    print("🎤 PyAudio terminated")
                    self.audio = None
                except Exception as e:
                    print(f"⚠️ Error terminating PyAudio: {e}")
                    self.audio = None
            
            # Wait for audio thread with timeout
            if self.audio_thread and self.audio_thread.is_alive():
                try:
                    self.audio_thread.join(timeout=1.0)
                    if self.audio_thread.is_alive():
                        print("⚠️ Audio thread still alive after timeout")
                    else:
                        print("🧵 Audio thread terminated")
                except Exception as e:
                    print(f"⚠️ Error joining audio thread: {e}")
            
            self.is_running = False
            print("✅ Cleanup completed")

if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    
    transcriber = AssemblyAIRealtimeTranscriber(api_key)
    transcriber.start()
