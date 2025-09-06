import os
import json
import threading
import websocket
import pyaudio
import assemblyai as aai
from dotenv import load_dotenv

# Load API key
load_dotenv()
KEY = os.getenv("ASSEMBLYAI_API_KEY")
aai.settings.api_key = KEY


class AudioTranscriber:

    def __init__(self, audio_file=None, mode="file"):
        """
        mode = "file" for pre-recorded file transcription
        mode = "live" for real-time microphone transcription
        """
        self.audio_file = audio_file
        self.mode = mode
        self.api_key = KEY
        self.live_url = "wss://api.assemblyai.com/v2/realtime/ws?sample_rate=16000"

    def transcribe_file(self):
        """Transcribe a pre-recorded file"""
        config = aai.TranscriptionConfig(speech_model=aai.SpeechModel.best)
        transcript = aai.Transcriber(config=config).transcribe(self.audio_file)

        if transcript.status == "error":
            raise RuntimeError(f"Transcription failed: {transcript.error}")

        return transcript.text

    def transcribe_live(self):
        """Real-time transcription from microphone"""

        def on_open(ws):
            print("🔊 Connected, start speaking...")

            # ✅ IMPORTANT: Tell AssemblyAI we're starting a realtime session
            ws.send(json.dumps({"event": "start", "sample_rate": 16000}))

            # Setup PyAudio stream
            stream = pyaudio.PyAudio().open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=3200
            )

            def stream_audio():
                while True:
                    data = stream.read(3200, exception_on_overflow=False)
                    ws.send(data, websocket.ABNF.OPCODE_BINARY)

            threading.Thread(target=stream_audio, daemon=True).start()

        def on_message(ws, message):
            data = json.loads(message)
            if "text" in data and data["text"].strip():
                print("Transcript:", data["text"])

        def on_error(ws, error):
            print("❌ Error:", error)

        def on_close(ws, code, msg):
            print(f"🔒 Connection closed: {code} {msg}")

        headers = {"Authorization": self.api_key}
        ws = websocket.WebSocketApp(
            self.live_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close,
            header=headers
        )

        ws.run_forever()

    def transcribe(self):
        """Unified entry point"""
        if self.mode == "file":
            return self.transcribe_file()
        elif self.mode == "live":
            self.transcribe_live()
        else:
            raise ValueError("Mode must be 'file' or 'live'")


if __name__ == "__main__":
    # Example 1: File transcription
    # audio_file = r"C:\Users\sudip\Gemma-3n-impact\remote\server\uploads\sample01.mp3"
    # file_transcriber = AudioTranscriber(audio_file=audio_file, mode="file")
    # text = file_transcriber.transcribe()
    # print("\nFinal Transcript:", text)

    # Example 2: Live transcription (mic)
    live_transcriber = AudioTranscriber(mode="live")
    live_transcriber.transcribe()
