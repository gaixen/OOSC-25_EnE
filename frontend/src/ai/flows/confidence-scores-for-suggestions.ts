'use server';

/**
 * @fileOverview This file defines a Genkit flow for assigning confidence scores to AI suggestions.
 *
 * - assessSuggestionConfidence - A function that assesses the confidence level of a given AI suggestion.
 * - AssessSuggestionConfidenceInput - The input type for the assessSuggestionConfidence function.
 * - AssessSuggestionConfidenceOutput - The return type for the assessSuggestionConfidence function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const AssessSuggestionConfidenceInputSchema = z.object({
  suggestion: z.string().describe('The AI suggestion to be assessed.'),
  agentName: z.string().describe('The name of the agent that generated the suggestion.'),
  source: z.string().describe('The source of the information used to generate the suggestion.'),
  provenance: z.string().describe('The provenance or agent trace for the suggestion.'),
});
export type AssessSuggestionConfidenceInput = z.infer<typeof AssessSuggestionConfidenceInputSchema>;

const AssessSuggestionConfidenceOutputSchema = z.object({
  confidenceScore: z.number().describe('The confidence score (0-1) for the AI suggestion.'),
  shouldEmployTool: z.boolean().describe('Whether a tool should be employed based on the suggestion.'),
});
export type AssessSuggestionConfidenceOutput = z.infer<typeof AssessSuggestionConfidenceOutputSchema>;

export async function assessSuggestionConfidence(
  input: AssessSuggestionConfidenceInput
): Promise<AssessSuggestionConfidenceOutput> {
  return assessSuggestionConfidenceFlow(input);
}

const assessSuggestionConfidencePrompt = ai.definePrompt({
  name: 'assessSuggestionConfidencePrompt',
  input: {schema: AssessSuggestionConfidenceInputSchema},
  output: {schema: AssessSuggestionConfidenceOutputSchema},
  prompt: `You are an AI assistant that assesses the confidence level of AI suggestions for sales representatives.\n\nYou will receive an AI suggestion, the agent that generated it, the source of the information, and the agent provenance.\nBased on this information, you will determine a confidence score (between 0 and 1) for the suggestion. Higher scores indicate greater reliability.\n\nYou will also determine whether a tool should be employed based on the suggestion; set the shouldEmployTool field appropriately.\n\nSuggestion: {{{suggestion}}}\nAgent: {{{agentName}}}\nSource: {{{source}}}\nPovenance: {{{provenance}}}\n\nConfidence Score (0-1):\nShould Employ Tool: `,
});

const assessSuggestionConfidenceFlow = ai.defineFlow(
  {
    name: 'assessSuggestionConfidenceFlow',
    inputSchema: AssessSuggestionConfidenceInputSchema,
    outputSchema: AssessSuggestionConfidenceOutputSchema,
  },
  async input => {
    const {output} = await assessSuggestionConfidencePrompt(input);
    return output!;
  }
);
