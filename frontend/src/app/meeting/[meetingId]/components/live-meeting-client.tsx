"use client";

import { useState, useEffect, useRef } from 'react';
import type { Suggestion, TranscriptLine } from '@/types';
import { mockTranscript } from '@/lib/mock-data';
import { generateAISuggestions } from '@/ai/flows/ai-suggestions-during-meeting';

import { VideoPlaceholder } from './video-placeholder';
import { LiveTranscript } from './live-transcript';
import { AiSuggestions } from './ai-suggestions';

let transcriptCounter = 0;
const agentSimulationSequence = ["STT Agent", "Entity Extraction", "Knowledge Retrieval", "Planner Agent"];

export default function LiveMeetingClient() {
  const [transcript, setTranscript] = useState<TranscriptLine[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [isSimulating, setIsSimulating] = useState(true);
  const [currentAgent, setCurrentAgent] = useState('Idle');

  const simulationIntervalRef = useRef<NodeJS.Timeout | null>(null);

  const runSimulationStep = async () => {
    // 1. Simulate agent activity
    let agentIndex = 0;
    const agentInterval = setInterval(() => {
      if (agentIndex < agentSimulationSequence.length) {
        setCurrentAgent(agentSimulationSequence[agentIndex]);
        agentIndex++;
      } else {
        clearInterval(agentInterval);
        setCurrentAgent('Idle');
      }
    }, 1000);

    // 2. Add new transcript line
    const newTranscriptLine = {
      ...mockTranscript[transcriptCounter % mockTranscript.length],
      id: transcriptCounter,
    };
    transcriptCounter++;

    setTranscript(prev => [...prev, newTranscriptLine]);

    // 3. Generate AI suggestions based on recent transcript
    const recentTranscriptText = [...transcript, newTranscriptLine]
      .slice(-3)
      .map(t => `${t.speaker}: ${t.text}`)
      .join('\n');

    try {
      // Delay suggestion generation to allow agent simulation to be visible
      setTimeout(async () => {
        const result = await generateAISuggestions({ transcript: recentTranscriptText });
        if (result.suggestions) {
          const newSuggestions = result.suggestions.map(s => ({
            ...s,
            id: `sugg-${Date.now()}-${Math.random()}`,
             provenance: `Factual Step: Entity Extraction detected "Acme Corp"\nPrompt to LLM: "Generate talking points about Acme"\nRetrieved Evidence: "Acme Corp's Q3 revenue fell short of expectations."`
          }));
          setSuggestions(prev => [...newSuggestions, ...prev].slice(0, 10)); // Keep last 10 suggestions
        }
         clearInterval(agentInterval);
         setCurrentAgent('Idle');
      }, agentSimulationSequence.length * 1000);

    } catch (error) {
      console.error("Error generating AI suggestions:", error);
      clearInterval(agentInterval);
      setCurrentAgent('Error');
    }
  };

  useEffect(() => {
    if (isSimulating) {
      runSimulationStep();
      simulationIntervalRef.current = setInterval(runSimulationStep, 8000);
    } else {
      if (simulationIntervalRef.current) {
        clearInterval(simulationIntervalRef.current);
      }
    }

    return () => {
      if (simulationIntervalRef.current) {
        clearInterval(simulationIntervalRef.current);
      }
    };
  }, [isSimulating]);

  return (
    <div className="grid md:grid-cols-3 gap-4 p-4 h-full">
      <div className="md:col-span-2 flex flex-col gap-4 h-full overflow-hidden">
        <div className="flex-shrink-0">
          <VideoPlaceholder />
        </div>
        <div className="flex-grow min-h-0">
          <LiveTranscript transcript={transcript} />
        </div>
      </div>

      <div className="md:col-span-1 h-full overflow-hidden">
        <AiSuggestions suggestions={suggestions} currentAgent={currentAgent} />
      </div>
    </div>
  );
}
