import { useEffect, useRef } from 'react';
import { FileText } from 'lucide-react';
import type { TranscriptLine } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { cn } from '@/lib/utils';

interface LiveTranscriptProps {
  transcript: TranscriptLine[];
}

export function LiveTranscript({ transcript }: LiveTranscriptProps) {
  const scrollAreaRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTo({ top: scrollAreaRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [transcript]);

  return (
    <Card className="h-full flex flex-col shadow-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="text-primary" />
          <span>Live Transcript</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-grow p-0 overflow-hidden">
        <ScrollArea className="h-full" ref={scrollAreaRef}>
          <div className="p-4 space-y-4">
            {transcript.map((line) => (
              <div key={line.id} className="flex flex-col animate-in fade-in duration-500">
                <p className={cn(
                    "font-bold text-sm",
                    line.speaker === 'Sales Rep' ? 'text-accent-foreground/80' : 'text-primary'
                  )}>
                  {line.speaker}
                </p>
                <p className="text-foreground">{line.text}</p>
              </div>
            ))}
          </div>
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
