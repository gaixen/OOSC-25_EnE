import os
import json
import threading
import time
import wave
from urllib.parse import urlencode
from datetime import datetime
import pyaudio
import websocket
from dotenv import load_dotenv


class AssemblyAIRealtimeTranscriber:
    def __init__(self, api_key: str, sample_rate: int = 16000, frames_per_buffer: int = 800):
        self.api_key = api_key
        self.sample_rate = sample_rate
        self.frames_per_buffer = frames_per_buffer
        self.channels = 1
        self.format = pyaudio.paInt16

        # WebSocket endpoint
        connection_params = {"sample_rate": self.sample_rate, "format_turns": True}
        base_url = "wss://streaming.assemblyai.com/v3/ws"
        self.api_endpoint = f"{base_url}?{urlencode(connection_params)}"

        # Audio/WebSocket state
        self.audio = None
        self.stream = None
        self.ws_app = None
        self.audio_thread = None
        self.stop_event = threading.Event()

        # Recording state
        self.recorded_frames = []
        self.recording_lock = threading.Lock()

    # ---------------- Event Handlers ---------------- #
    def on_open(self, ws):
        print("✅ WebSocket connection opened.")
        print(f"Connected to: {self.api_endpoint}")

        def stream_audio():
            print("🎙️ Starting audio streaming...")
            while not self.stop_event.is_set():
                try:
                    audio_data = self.stream.read(
                        self.frames_per_buffer, exception_on_overflow=False
                    )
                    with self.recording_lock:
                        self.recorded_frames.append(audio_data)

                    ws.send(audio_data, websocket.ABNF.OPCODE_BINARY)
                except Exception as e:
                    print(f"⚠️ Error streaming audio: {e}")
                    break
            print("🛑 Audio streaming stopped.")

        self.audio_thread = threading.Thread(target=stream_audio, daemon=True)
        self.audio_thread.start()

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            msg_type = data.get("type")

            if msg_type == "Begin":
                session_id = data.get("id")
                expires_at = data.get("expires_at")
                print(
                    f"\n🔗 Session started: ID={session_id}, "
                    f"ExpiresAt={datetime.fromtimestamp(expires_at)}"
                )

            elif msg_type == "Turn":
                transcript = data.get("transcript", "")
                formatted = data.get("turn_is_formatted", False)

                if formatted:
                    print("\r" + " " * 80 + "\r", end="")
                    print(f"📝 {transcript}")
                else:
                    print(f"\r{transcript}", end="")

            elif msg_type == "Termination":
                print(
                    f"\n🔒 Session terminated. "
                    f"Audio Duration={data.get('audio_duration_seconds', 0)}s, "
                    f"Session Duration={data.get('session_duration_seconds', 0)}s"
                )

        except Exception as e:
            print(f"⚠️ Error handling message: {e}")

    def on_error(self, ws, error):
        print(f"\n❌ WebSocket Error: {error}")
        self.stop_event.set()

    def on_close(self, ws, code, msg):
        print(f"\n🔌 WebSocket Disconnected: Code={code}, Msg={msg}")
        self.save_wav_file()
        self.cleanup()

    # ---------------- Core Methods ---------------- #
    def start(self):
        """Start transcription session"""
        self.audio = pyaudio.PyAudio()

        try:
            self.stream = self.audio.open(
                input=True,
                frames_per_buffer=self.frames_per_buffer,
                channels=self.channels,
                format=self.format,
                rate=self.sample_rate,
            )
            print("🎤 Microphone stream opened. Speak into your mic.")
        except Exception as e:
            print(f"❌ Error opening microphone: {e}")
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

        ws_thread = threading.Thread(target=self.ws_app.run_forever, daemon=True)
        ws_thread.start()

        try:
            while ws_thread.is_alive():
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\n⏹️ Ctrl+C received, stopping...")
            self.stop_event.set()
            if self.ws_app and self.ws_app.sock and self.ws_app.sock.connected:
                try:
                    self.ws_app.send(json.dumps({"type": "Terminate"}))
                    time.sleep(2)
                except Exception as e:
                    print(f"⚠️ Error sending terminate: {e}")
            if self.ws_app:
                self.ws_app.close()
            ws_thread.join(timeout=2)

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
        """Release resources"""
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
        print("🧹 Cleanup complete.")

if __name__ == "__main__":
    load_dotenv()
    api_key = os.getenv("ASSEMBLYAI_API_KEY")
    
    transcriber = AssemblyAIRealtimeTranscriber(api_key)
    transcriber.start()
