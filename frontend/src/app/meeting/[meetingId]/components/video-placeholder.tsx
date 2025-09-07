"use client";

import { useState, useRef, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Video, Mic, PhoneOff, VideoOff, MicOff, Phone } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

interface VideoPlaceholderProps {
  onTranscription?: (text: string) => void;
  sessionId?: string;
}

export function VideoPlaceholder({ onTranscription, sessionId }: VideoPlaceholderProps) {
  const [isMicOn, setIsMicOn] = useState(false);
  const [isCameraOn, setIsCameraOn] = useState(true);
  const [isCallActive, setIsCallActive] = useState(true);
  const [isEndingCall, setIsEndingCall] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  
  const router = useRouter();
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      streamRef.current = stream;
      
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      
      mediaRecorder.ondataavailable = async (event) => {
        if (event.data.size > 0 && onTranscription && sessionId) {
          const formData = new FormData();
          formData.append('audio', event.data);
          formData.append('session_id', sessionId);
          
          try {
            const response = await fetch('http://localhost:8000/api/process-audio', {
              method: 'POST',
              body: formData,
            });
            const result = await response.json();
            if (result.transcription) {
              onTranscription(result.transcription);
            }
          } catch (error) {
            console.error('Audio processing error:', error);
          }
        }
      };
      
      mediaRecorder.start(1000);
      setIsRecording(true);
    } catch (error) {
      console.error('Microphone access error:', error);
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach(track => track.stop());
    }
  };

  const toggleMicrophone = () => {
    const newMicState = !isMicOn;
    setIsMicOn(newMicState);
    
    if (onTranscription && sessionId) {
      // Send voice control message via WebSocket instead of audio upload
      fetch('http://localhost:8000/api/voice-control', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          action: newMicState ? 'start' : 'stop'
        })
      });
    }
  };

  useEffect(() => {
    return () => {
      stopRecording();
    };
  }, []);

  const handleEndCall = () => {
    stopRecording();
    setIsEndingCall(true);
    setTimeout(() => {
      router.push('/');
    }, 1000);
  };

  return (
    <Card 
      className={cn(
        "aspect-video w-full flex flex-col items-center justify-center bg-card-foreground/5 p-4 relative overflow-hidden transition-all duration-1000",
        isEndingCall && "scale-90 opacity-0"
      )}
    >
       <div className="absolute inset-0 bg-grid-slate-100 [mask-image:linear-gradient(0deg,#fff,rgba(255,255,255,0.6))] dark:bg-grid-slate-700/25 dark:[mask-image:linear-gradient(0deg,rgba(255,255,255,0.1),rgba(255,255,255,0.5))]"></div>
      <div className="text-center z-10">
        <Video className="h-16 w-16 text-muted-foreground mx-auto" />
        <p className="mt-4 text-lg font-medium text-foreground">Live Video Feed</p>
        <p className="text-sm text-muted-foreground">Meeting in progress...</p>
      </div>
      <div className="absolute bottom-4 z-10 flex items-center gap-2">
          <Button 
            variant="secondary" 
            size="icon" 
            className={cn(
              "rounded-full h-12 w-12 bg-background/80 backdrop-blur-sm",
              isMicOn && "bg-red-500 hover:bg-red-600 text-white",
              isRecording && "animate-pulse"
            )}
            onClick={toggleMicrophone}
            aria-label={isMicOn ? "Mute microphone" : "Unmute microphone"}
          >
            {isMicOn ? <Mic className="h-6 w-6" /> : <MicOff className="h-6 w-6" />}
          </Button>
          <Button 
            variant="secondary" 
            size="icon" 
            className="rounded-full h-12 w-12 bg-background/80 backdrop-blur-sm"
            onClick={() => setIsCameraOn(prev => !prev)}
            aria-label={isCameraOn ? "Turn off camera" : "Turn on camera"}
          >
            {isCameraOn ? <Video className="h-6 w-6" /> : <VideoOff className="h-6 w-6" />}
          </Button>
          
          {!isCallActive && (
            <Button 
              size="icon" 
              className="rounded-full h-12 w-12 bg-green-500 hover:bg-green-600 text-white"
              onClick={() => setIsCallActive(true)}
              aria-label="Start call"
            >
              <Phone className="h-6 w-6" />
            </Button>
          )}

          {isCallActive && (
             <Button 
              variant="destructive" 
              size="icon" 
              className="rounded-full h-12 w-12"
              onClick={handleEndCall}
              aria-label="End call"
            >
              <PhoneOff className="h-6 w-6" />
            </Button>
          )}
        </div>
    </Card>
  );
}
