"use client";

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Video, Mic, PhoneOff, VideoOff, MicOff, Phone } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { cn } from '@/lib/utils';

export function VideoPlaceholder() {
  const [isMicOn, setIsMicOn] = useState(true);
  const [isCameraOn, setIsCameraOn] = useState(true);
  const [isCallActive, setIsCallActive] = useState(true);
  const [isEndingCall, setIsEndingCall] = useState(false);
  const router = useRouter();

  const handleEndCall = () => {
    setIsEndingCall(true);
    setTimeout(() => {
      router.push('/');
    }, 1000); // Corresponds to animation duration
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
            className="rounded-full h-12 w-12 bg-background/80 backdrop-blur-sm"
            onClick={() => setIsMicOn(prev => !prev)}
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
