import type { Meeting, TranscriptLine } from "@/types";

export const meetings: Meeting[] = [
  { id: '1', title: 'Q4 Strategy Session with Acme Corp', date: '2024-07-20T10:00:00Z', status: 'live' },
  { id: '2', title: 'Project Phoenix Kickoff', date: '2024-07-21T14:00:00Z', status: 'upcoming' },
  { id: '3', title: 'Marketing Budget Review', date: '2024-07-22T11:00:00Z', status: 'upcoming' },
  { id: '4', title: 'Q3 Performance Analysis', date: '2024-07-15T09:00:00Z', status: 'completed' },
  { id: '5', title: 'Alpha Project Debrief', date: '2024-07-12T16:00:00Z', status: 'completed' },
];

export const mockTranscript: Pick<TranscriptLine, 'speaker' | 'text'>[] = [
    { speaker: "Sales Rep", text: "Thanks for joining today. To start, could you walk me through your current workflow?" },
    { speaker: "Customer", text: "Sure. We're currently using a mix of spreadsheets and manual data entry, which is becoming inefficient." },
    { speaker: "Sales Rep", text: "I see. Many of our clients face similar challenges. Our platform can automate a lot of that." },
    { speaker: "Customer", text: "That sounds promising. How does the pricing work?" },
    { speaker: "Sales Rep", text: "We have a tiered pricing model. Based on your team size, the Pro plan would be a great fit." },
    { speaker: "Customer", text: "What about integration with our existing CRM?" },
    { speaker: "Sales Rep", text: "We offer seamless integration with all major CRM platforms, including the one you use." },
    { speaker: "Customer", text: "Excellent. Can we schedule a follow-up demo for the rest of my team?" },
    { speaker: "Sales Rep", text: "Absolutely. I'll send over a calendar invite right after this call." },
    { speaker: "Customer", text: "Great, looking forward to it." },
];
