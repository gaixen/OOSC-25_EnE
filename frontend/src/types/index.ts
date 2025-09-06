import type { GenerateAISuggestionsOutput } from "@/ai/flows/ai-suggestions-during-meeting";

export type Meeting = {
  id: string;
  title: string;
  date: string;
  status: 'upcoming' | 'live' | 'completed';
};

export type Suggestion = GenerateAISuggestionsOutput['suggestions'][0] & { id: string };

export type TranscriptLine = {
  id: number;
  speaker: 'Customer' | 'Sales Rep';
  text: string;
};
