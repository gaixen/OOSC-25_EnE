"use client";

import { useState, useEffect, useRef } from 'react';
import type { Suggestion, TranscriptLine } from '@/types';

import { VideoPlaceholder } from './video-placeholder';
import { LiveTranscript } from './live-transcript';
import { AiSuggestions } from './ai-suggestions';
import { CurrentAgentIndicator } from './current-agent-indicator';

export default function LiveMeetingClient() {
  const [transcript, setTranscript] = useState<TranscriptLine[]>([]);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [currentAgent, setCurrentAgent] = useState('Idle');
  const [agentStatuses, setAgentStatuses] = useState<Record<string, any>>({});
  const [provenanceChain, setProvenanceChain] = useState<any[]>([]);
  const [sessionId, setSessionId] = useState<string>('');
  const [isProcessing, setIsProcessing] = useState(false);
  
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let reconnectTimeout: NodeJS.Timeout;
    let reconnectAttempts = 0;
    const maxReconnectAttempts = 5;

    const initSession = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/start-meeting', { method: 'POST' });
        const data = await response.json();
        setSessionId(data.session_id);
        
        connectWebSocket(data.session_id);
      } catch (error) {
        console.error('❌ Failed to start meeting session:', error);
        // Retry session initialization
        if (reconnectAttempts < maxReconnectAttempts) {
          reconnectTimeout = setTimeout(() => {
            reconnectAttempts++;
            console.log(`🔄 Retrying session initialization (attempt ${reconnectAttempts})`);
            initSession();
          }, 2000 * reconnectAttempts);
        }
      }
    };

    const connectWebSocket = (sessionId: string) => {
      console.log(`🔌 Connecting WebSocket for session: ${sessionId}`);
      
      const ws = new WebSocket(`ws://localhost:8000/ws/${sessionId}`);
      wsRef.current = ws;
      
      ws.onopen = () => {
        console.log('✅ WebSocket connected successfully');
        reconnectAttempts = 0; // Reset attempts on successful connection
      };
      
      ws.onmessage = (event) => {
        const message = JSON.parse(event.data);
        console.log('📨 WebSocket message received:', message);
        
        if (message.type === 'suggestions') {
          // Stop processing when suggestions are received
          setIsProcessing(false);
          
          // Handle the new enhanced suggestion format
          const formattedSuggestions = message.data.map((item: any) => ({
            id: item.id || Math.random().toString(36),
            talkingPoint: item.talkingPoint || item.suggestion || item.text || item,
            confidenceScore: item.confidenceScore || item.confidence || 0.8,
            source: item.source || (item.references ? item.references.join(', ') : 'AI Generated'),
            agentName: item.agentName || 'AI Assistant',
            provenance: item.provenance || `Generated suggestion with ${item.confidenceScore || 0.8} confidence`,
            context: item.context || '',
            type: item.type || 'insight'
          }));
          
          console.log('🤖 Formatted suggestions:', formattedSuggestions);
          setSuggestions(formattedSuggestions);
          
          // Update current agent and provenance
          if (message.current_agent) {
            setCurrentAgent(message.current_agent);
          }
          if (message.provenance_chain) {
            setProvenanceChain(message.provenance_chain);
          }
          
        } else if (message.type === 'transcription') {
          setTranscript(prev => [...prev, {
            id: Date.now(),
            speaker: 'Customer',
            text: message.data.text,
            timestamp: new Date().toLocaleTimeString()
          }]);
          
        } else if (message.type === 'agent_status') {
          console.log('🤖 Agent status update received:', message.data);
          // Handle agent status updates - SAVE ALL DATA INCLUDING RESULTS
          const { agent_name, status, timestamp, results } = message.data;
          setAgentStatuses(prev => ({
            ...prev,
            [agent_name]: { agent_name, status, timestamp, results }
          }));
          
          // Update current agent if it's working
          if (status === 'working') {
            setCurrentAgent(agent_name);
            // Start processing when any agent starts working (except entity_extractor which is first)
            if (agent_name === 'suggestion_generator' || agent_name === 'ranking_agent') {
              setIsProcessing(true);
            }
          }
        }
      };

      ws.onerror = (error) => {
        console.error('❌ WebSocket error:', error);
      };

      ws.onclose = (event) => {
        console.log(`🔌 WebSocket closed: code=${event.code}, reason=${event.reason}`);
        wsRef.current = null;
        
        // Attempt to reconnect if not a clean close
        if (event.code !== 1000 && reconnectAttempts < maxReconnectAttempts) {
          reconnectAttempts++;
          console.log(`🔄 Attempting WebSocket reconnection (attempt ${reconnectAttempts})`);
          reconnectTimeout = setTimeout(() => {
            if (sessionId) {
              connectWebSocket(sessionId);
            }
          }, 1000 * reconnectAttempts);
        }
      };
    };

    initSession();

    return () => {
      if (reconnectTimeout) {
        clearTimeout(reconnectTimeout);
      }
      if (wsRef.current) {
        wsRef.current.close(1000, 'Component unmounting');
      }
    };
  }, []);

  const handleTextInput = (text: string) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN && text.trim()) {
      console.log('📤 Sending utterance via WebSocket:', text);
      
      // Start processing when user sends input
      setIsProcessing(true);
      setSuggestions([]); // Clear previous suggestions
      
      wsRef.current.send(JSON.stringify({
        type: 'utterance',
        text: text
      }));
      
      setTranscript(prev => [...prev, {
        id: Date.now(),
        speaker: 'Customer',
        text: text,
        timestamp: new Date().toLocaleTimeString()
      }]);
    } else {
      console.warn('⚠️ WebSocket not ready for sending:', {
        wsExists: !!wsRef.current,
        readyState: wsRef.current?.readyState,
        text: text.trim()
      });
    }
  };

  const handleTranscription = (text: string) => {
    if (text.trim()) {
      handleTextInput(text);
    }
  };

  return (
    <div className="grid md:grid-cols-3 gap-4 p-4 h-full">
      <div className="md:col-span-2 flex flex-col gap-4 h-full overflow-hidden">
        <div className="flex-shrink-0">
          <VideoPlaceholder onTranscription={handleTranscription} sessionId={sessionId} />
        </div>
        <div className="flex-grow overflow-hidden">
          <LiveTranscript transcript={transcript} onTextInput={handleTextInput} />
        </div>
      </div>
      <div className="flex flex-col h-full overflow-hidden gap-4">
        <div className="flex-shrink-0">
          <CurrentAgentIndicator agentStatuses={agentStatuses} currentAgent={currentAgent} />
        </div>
        <div className="flex-grow overflow-hidden">
          <AiSuggestions 
            suggestions={suggestions} 
            currentAgent={currentAgent}
            isProcessing={isProcessing}
          />
        </div>
      </div>
    </div>
  );
}
