import { Bot, Loader } from "lucide-react";

interface CurrentAgentIndicatorProps {
  agentName: string;
}

export function CurrentAgentIndicator({ agentName }: CurrentAgentIndicatorProps) {
  return (
    <div className="p-4 border-b bg-secondary/50">
      <h3 className="text-sm font-semibold text-muted-foreground mb-2">CURRENT AGENT</h3>
      <div className="flex items-center gap-3">
        <div className="flex items-center justify-center h-8 w-8 rounded-full bg-primary/20 text-primary">
          <Bot className="h-5 w-5" />
        </div>
        <div>
          <p className="font-bold text-foreground">{agentName}</p>
          <div className="flex items-center gap-2 text-primary">
            <Loader className="h-4 w-4 animate-spin" />
            <span className="text-xs font-medium">Processing...</span>
          </div>
        </div>
      </div>
    </div>
  );
}
