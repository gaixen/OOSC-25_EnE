import Link from "next/link";
import { Video, Calendar, ArrowRight } from "lucide-react";
import type { Meeting } from "@/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface MeetingsCardProps {
  title: string;
  meetings: Meeting[];
}

export function MeetingsCard({ title, meetings }: MeetingsCardProps) {
  const isUpcoming = title.includes("Upcoming");

  return (
    <Card className="shadow-lg hover:shadow-xl transition-shadow duration-300">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Video className="text-primary" />
          <span>{title}</span>
        </CardTitle>
      </CardHeader>
      <CardContent>
        {meetings.length > 0 ? (
          <ul className="space-y-4">
            {meetings.map((meeting) => (
              <li key={meeting.id} className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 p-4 rounded-lg bg-secondary/50 border">
                <div className="flex-grow">
                  <p className="font-semibold text-foreground">{meeting.title}</p>
                  <div className="flex items-center gap-2 text-sm text-muted-foreground mt-1">
                    <Calendar className="h-4 w-4" />
                    <span>{new Date(meeting.date).toLocaleString()}</span>
                    {meeting.status === 'live' && <Badge variant="destructive" className="animate-pulse">Live</Badge>}
                  </div>
                </div>
                <Link href={`/meeting/${meeting.id}`}>
                  <Button className="w-full sm:w-auto" variant={isUpcoming ? "default" : "outline"}>
                    {meeting.status === "completed" ? "View" : meeting.status === "live" ? "Join" : "Go Live"}
                    <ArrowRight className="ml-2 h-4 w-4" />
                  </Button>
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <p className="text-muted-foreground text-center py-8">No meetings to display.</p>
        )}
      </CardContent>
    </Card>
  );
}
