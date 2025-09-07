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
        self.is_running = False
        
        print(f"🎤 AssemblyAI Transcriber initialized with callback: {self.on_transcript_callback is not None}")

    # ---------------- Event Handlers ---------------- #
    def on_open(self, ws):
        def stream_audio():
            while not self.stop_event.is_set():
                try:
                    if self.stream:
                        audio_data = self.stream.read(
                            self.frames_per_buffer, exception_on_overflow=False
                        )
                        with self.recording_lock:
                            self.recorded_frames.append(audio_data)
                        ws.send(audio_data, websocket.ABNF.OPCODE_BINARY)
                except Exception as e:
                    break

        self.audio_thread = threading.Thread(target=stream_audio, daemon=True)
        self.audio_thread.start()

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
        self.stop_event.set()

    def on_close(self, ws, code, msg):
        self.cleanup()

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
            return
            
        self.is_running = False
        self.stop_event.set()
        if self.ws_app and self.ws_app.sock and self.ws_app.sock.connected:
            try:
                self.ws_app.send(json.dumps({"type": "Terminate"}))
                time.sleep(0.1)
            except:
                pass
        if self.ws_app:
            self.ws_app.close()
        self.cleanup()

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
        self.stop_event.set()
        if self.stream:
            if self.stream.is_active():
                self.stream.stop_stream()
            self.stream.close()
            self.stream = None
        if self.audio:
            self.audio.terminate()
            self.audio = None
        if self.audio_thread and self.audio_thread.is_alive():
            self.audio_thread.join(timeout=1.0)

if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    
    transcriber = AssemblyAIRealtimeTranscriber(api_key)
    transcriber.start()
