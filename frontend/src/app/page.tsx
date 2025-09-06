import { MeetingsCard } from "@/components/dashboard/meetings-card";
import { Logo } from "@/components/logo";
import { meetings } from "@/lib/mock-data";
import type { Meeting } from "@/types";

export default function DashboardPage() {
  const currentMeetings = meetings.filter(
    (m) => m.status === "upcoming" || m.status === "live"
  );
  const previousMeetings = meetings.filter((m) => m.status === "completed");

  return (
    <main className="container mx-auto p-4 md:p-8">
      <div className="flex flex-col items-center justify-center space-y-8">
        <Logo />
        <div className="w-full max-w-4xl grid grid-cols-1 md:grid-cols-2 gap-8">
          <MeetingsCard title="Current & Upcoming Meetings" meetings={currentMeetings} />
          <MeetingsCard title="Previous Meetings" meetings={previousMeetings} />
        </div>
      </div>
    </main>
  );
}
