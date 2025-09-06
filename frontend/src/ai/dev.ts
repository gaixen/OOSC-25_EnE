import { config } from 'dotenv';
config();

import '@/ai/flows/ai-suggestions-during-meeting.ts';
import '@/ai/flows/confidence-scores-for-suggestions.ts';
import '@/ai/flows/agent-provenance-tracking.ts';