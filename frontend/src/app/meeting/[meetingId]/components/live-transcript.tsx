import { useEffect, useRef, useState } from 'react';
import { FileText } from 'lucide-react';
import type { TranscriptLine } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface LiveTranscriptProps {
  transcript: TranscriptLine[];
  onTextInput: (text: string) => void;
}

export function LiveTranscript({ transcript, onTextInput }: LiveTranscriptProps) {
  const scrollAreaRef = useRef<HTMLDivElement>(null);
  const [inputText, setInputText] = useState('');

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTo({ top: scrollAreaRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [transcript]);

  const handleSubmit = () => {
    if (inputText.trim()) {
      onTextInput(inputText);
      setInputText('');
    }
  };

  return (
    <Card className="h-full flex flex-col shadow-md">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <FileText className="text-primary" />
          <span>Live Transcript</span>
        </CardTitle>
      </CardHeader>
      <CardContent className="flex-grow p-0 overflow-hidden flex flex-col">
        <ScrollArea className="flex-grow" ref={scrollAreaRef}>
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
        <div className="p-4 border-t flex gap-2">
          <Input
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Type your message..."
            onKeyPress={(e) => e.key === 'Enter' && handleSubmit()}
          />
          <Button onClick={handleSubmit}>Send</Button>
        </div>
      </CardContent>
    </Card>
  );
}
