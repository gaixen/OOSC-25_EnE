'use server';

/**
 * @fileOverview AI-powered suggestions during a live meeting for sales representatives.
 *
 * - generateAISuggestions - A function that generates AI suggestions for the live meeting.
 * - GenerateAISuggestionsInput - The input type for the generateAISuggestions function.
 * - GenerateAISuggestionsOutput - The return type for the generateAISuggestions function.
 */

import {ai} from '@/ai/genkit';
import {z} from 'genkit';

const GenerateAISuggestionsInputSchema = z.object({
  transcript: z
    .string()
    .describe('The current live transcript of the meeting.'),
});
export type GenerateAISuggestionsInput = z.infer<
  typeof GenerateAISuggestionsInputSchema
>;

const GenerateAISuggestionsOutputSchema = z.object({
  suggestions: z.array(
    z.object({
      talkingPoint: z.string().describe('The suggested talking point.'),
      confidenceScore: z
        .number()
        .describe('The confidence score of the suggestion (0-1).'),
      agentName: z.string().describe('The name of the agent that generated it.'),
      source: z.string().describe('The source of the information.'),
      provenance: z
        .string()
        .describe('The agent trace, detailing how the suggestion was generated.'),
    })
  ),
});
export type GenerateAISuggestionsOutput = z.infer<
  typeof GenerateAISuggestionsOutputSchema
>;

export async function generateAISuggestions(
  input: GenerateAISuggestionsInput
): Promise<GenerateAISuggestionsOutput> {
  return generateAISuggestionsFlow(input);
}

const prompt = ai.definePrompt({
  name: 'generateAISuggestionsPrompt',
  input: {schema: GenerateAISuggestionsInputSchema},
  output: {schema: GenerateAISuggestionsOutputSchema},
  prompt: `You are an AI-powered sales assistant providing real-time talking points during a live meeting.

  Based on the current meeting transcript, generate a list of relevant and helpful suggestions.

  Transcript: {{{transcript}}}
  `,
});

const generateAISuggestionsFlow = ai.defineFlow(
  {
    name: 'generateAISuggestionsFlow',
    inputSchema: GenerateAISuggestionsInputSchema,
    outputSchema: GenerateAISuggestionsOutputSchema,
  },
  async input => {
    const {output} = await prompt(input);
    return output!;
  }
);
