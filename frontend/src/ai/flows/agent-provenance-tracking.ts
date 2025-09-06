'use server';

/**
 * @fileOverview This file defines a Genkit flow for tracking the agent provenance of AI suggestions.
 *
 * The flow takes an AI suggestion as input and returns the provenance or agent trace,
 * detailing the generation flow from the initial agent (e.g., STT Agent) to the final agent (e.g., Planner).
 *
 * @param {string} suggestion - The AI suggestion to trace.
 * @returns {Promise<string>} - A promise that resolves to the agent provenance or trace.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const AgentProvenanceInputSchema = z.object({
  suggestion: z.string().describe('The AI suggestion to trace.'),
});
export type AgentProvenanceInput = z.infer<typeof AgentProvenanceInputSchema>;

const AgentProvenanceOutputSchema = z.string().describe('The agent provenance or trace for the suggestion.');
export type AgentProvenanceOutput = z.infer<typeof AgentProvenanceOutputSchema>;

export async function getAgentProvenance(input: AgentProvenanceInput): Promise<AgentProvenanceOutput> {
  return agentProvenanceFlow(input);
}

const prompt = ai.definePrompt({
  name: 'agentProvenancePrompt',
  input: {schema: AgentProvenanceInputSchema},
  output: {schema: AgentProvenanceOutputSchema},
  prompt: `Given the following AI suggestion, please provide a detailed provenance or agent trace, explaining how the suggestion was generated. Include all agents involved in the generation process, from the initial agent (e.g., STT Agent) to the final agent (e.g., Planner).

Suggestion: {{{suggestion}}}

Provenance:`,
});

const agentProvenanceFlow = ai.defineFlow(
  {
    name: 'agentProvenanceFlow',
    inputSchema: AgentProvenanceInputSchema,
    outputSchema: AgentProvenanceOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    return output!;
  }
);
