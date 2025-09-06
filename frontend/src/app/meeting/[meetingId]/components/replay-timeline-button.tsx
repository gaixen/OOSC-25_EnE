import { Button } from "@/components/ui/button";
import { History } from "lucide-react";

export function ReplayTimelineButton() {
    const handleReplay = () => {
        console.log("Starting replay of agent activity timeline...");
        // Placeholder for future replay functionality
    };

    return (
        <div className="p-4 border-t">
            <Button variant="outline" className="w-full" onClick={handleReplay}>
                <History className="mr-2 h-4 w-4" />
                Replay Timeline
            </Button>
        </div>
    );
}
