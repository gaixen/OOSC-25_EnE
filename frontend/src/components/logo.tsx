import { MessageSquareCode } from "lucide-react";

export function Logo() {
  return (
    <div className="flex items-center gap-2">
      <MessageSquareCode className="h-8 w-8 text-primary" />
      <h1 className="text-2xl font-bold text-foreground">
        Agentic Sales Stream
      </h1>
    </div>
  );
}
