import Link from "next/link";
import { ChevronLeft } from "lucide-react";
import { meetings } from "@/lib/mock-data";
import { Button } from "@/components/ui/button";
import LiveMeetingClient from "./components/live-meeting-client";

export default async function MeetingPage({ params }: { params: { meetingId: string } }) {
  const { meetingId } = await params;
  const meeting = meetings.find((m) => m.id === meetingId);

  if (!meeting) {
    return (
      <div className="flex flex-col items-center justify-center h-screen">
        <h1 className="text-2xl font-bold mb-4">Meeting not found</h1>
        <Button asChild>
          <Link href="/">Back to Dashboard</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-background">
      <header className="flex items-center p-4 border-b shrink-0">
        <Button variant="outline" size="icon" asChild>
          <Link href="/">
            <ChevronLeft className="h-4 w-4" />
          </Link>
        </Button>
        <div className="ml-4">
          <h1 className="text-lg font-semibold">{meeting.title}</h1>
          <p className="text-sm text-muted-foreground">
            {new Date(meeting.date).toLocaleString()}
          </p>
        </div>
      </header>
      <main className="flex-grow overflow-hidden">
        <LiveMeetingClient />
      </main>
    </div>
  );
}
