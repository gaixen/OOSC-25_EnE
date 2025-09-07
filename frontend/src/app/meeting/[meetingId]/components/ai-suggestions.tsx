import { Lightbulb, Bot, Database, BarChart, Route, ChevronsRight, FileText, BrainCircuit, Loader2 } from 'lucide-react';
import type { Suggestion } from '@/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Accordion, AccordionContent, AccordionItem, AccordionTrigger } from '@/components/ui/accordion';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { ReplayTimelineButton } from './replay-timeline-button';

interface AiSuggestionsProps {
  suggestions: Suggestion[];
  currentAgent: string;
  isProcessing?: boolean;
}

export function AiSuggestions({ suggestions, currentAgent, isProcessing = false }: AiSuggestionsProps) {
  const getConfidenceColor = (score: number) => {
    if (score > 0.8) return 'bg-green-500';
    if (score > 0.6) return 'bg-yellow-500';
    return 'bg-red-500';
  };

  return (
    <Card className="h-full flex flex-col shadow-md">
      <CardHeader className="p-4">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Lightbulb className="text-primary" />
          <span>AI Suggestions</span>
          {isProcessing && (
            <Loader2 className="h-4 w-4 animate-spin text-blue-500" />
          )}
        </CardTitle>
      </CardHeader>

      <CardContent className="flex-grow overflow-hidden p-0">
        <ScrollArea className="h-full">
          <div className="p-4">
          {isProcessing && suggestions.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground p-8">
              <Loader2 className="h-12 w-12 mb-4 animate-spin text-blue-500"/>
              <p className="font-semibold text-blue-600">Processing conversation...</p>
              <p className="text-sm">AI is analyzing entities and generating contextual suggestions.</p>
            </div>
          ) : suggestions.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center text-muted-foreground p-8">
              <Bot className="h-12 w-12 mb-4"/>
              <p className="font-semibold">Waiting for suggestions...</p>
              <p className="text-sm">AI will provide talking points as the conversation progresses.</p>
            </div>
          ) : (
            <Accordion type="single" collapsible className="w-full">
              {suggestions.map((s) => (
                <AccordionItem value={s.id} key={s.id} className="border-b-0 mb-2 bg-background rounded-lg border">
                  <AccordionTrigger className="p-4 text-left hover:no-underline rounded-lg w-full data-[state=open]:bg-secondary/50">
                    <div className="w-full flex flex-col gap-2">
                      <p className="font-semibold text-foreground leading-tight">{s.talkingPoint}</p>
                      <div className="flex items-center gap-4 text-xs text-muted-foreground flex-wrap">
                        <div className="flex items-center gap-1.5">
                          <BarChart className="h-3 w-3" />
                           <span>Confidence:</span>
                          <span className={`font-semibold ${getConfidenceColor(s.confidenceScore).replace('bg-', 'text-')}`}>
                             {(s.confidenceScore * 100).toFixed(0)}%
                          </span>
                        </div>
                         <div className="flex items-center gap-1.5">
                          <Bot className="h-3 w-3" />
                          <span>Agent: {s.agentName}</span>
                        </div>
                      </div>
                       <div className="flex items-center gap-1.5 text-xs text-muted-foreground">
                          <Database className="h-3 w-3" />
                          <span>Sources: {s.source}</span>
                        </div>
                    </div>
                  </AccordionTrigger>
                  <AccordionContent className="p-4 pt-2">
                    <div className="flex items-center gap-2 font-semibold mb-3 text-foreground text-sm">
                      <Route className="h-4 w-4 text-primary"/>
                      Provenance Trace
                    </div>
                    <ol className="relative border-l border-primary/20 ml-2 space-y-4">                  
                      {s.provenance.split('\n').filter(line => line.trim()).map((line, index) => {
                        const Icon = line.includes('Prompt') ? BrainCircuit : line.includes('Evidence') ? FileText : ChevronsRight;
                        return (
                           <li className="ml-6" key={index}>
                            <span className="absolute flex items-center justify-center w-6 h-6 bg-primary/20 rounded-full -left-3 ring-4 ring-background">
                              <Icon className="w-3 h-3 text-primary" />
                            </span>
                            <p className="text-xs text-muted-foreground font-mono">{line}</p>
                          </li>
                        )
                      })}
                    </ol>
                  </AccordionContent>
                </AccordionItem>
              ))}
            </Accordion>
          )}
          </div>
        </ScrollArea>
      </CardContent>

      <ReplayTimelineButton />
    </Card>
  );
}
