import { useParams } from 'react-router-dom';
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ExternalLink } from "lucide-react";

const mockActivity = {
  id: "1",
  title: "Adventure MUD",
  thumbnail: "https://images.unsplash.com/photo-1526481280693-3bfa7568e0f3?w=800&auto=format&fit=crop",
  description: "Learn Japanese through text-based adventure games. Immerse yourself in interactive stories while learning vocabulary and grammar.",
  sessions: [
    {
      id: "1",
      groupName: "Core Verbs",
      groupId: "1",
      startTime: "2024-03-15 09:30 AM",
      endTime: "2024-03-15 10:15 AM",
      reviewItems: 25
    }
  ]
};

export default function StudyActivity() {
  const { id } = useParams();

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <img
            src={mockActivity.thumbnail}
            alt={mockActivity.title}
            className="w-full h-64 object-cover rounded-t-lg"
          />
          <CardTitle className="text-2xl mt-4">{mockActivity.title}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground mb-4">{mockActivity.description}</p>
          <Button
            variant="destructive"
            onClick={() => window.open(`http://localhost:8081?group_id=${id}`, '_blank')}
          >
            <ExternalLink className="h-4 w-4 mr-2" />
            Launch Activity
          </Button>
        </CardContent>
      </Card>

      <div>
        <h2 className="text-xl font-semibold mb-4">Recent Sessions</h2>
        <div className="rounded-md border">
          <table className="w-full">
            <thead>
              <tr className="border-b bg-muted/50">
                <th className="p-4 text-left">Group Name</th>
                <th className="p-4 text-left">Start Time</th>
                <th className="p-4 text-left">End Time</th>
                <th className="p-4 text-left">Review Items</th>
              </tr>
            </thead>
            <tbody>
              {mockActivity.sessions.map((session) => (
                <tr key={session.id} className="border-b">
                  <td className="p-4">
                    <a
                      href={`/groups/${session.groupId}`}
                      className="text-primary hover:underline"
                    >
                      {session.groupName}
                    </a>
                  </td>
                  <td className="p-4">{session.startTime}</td>
                  <td className="p-4">{session.endTime}</td>
                  <td className="p-4">{session.reviewItems}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}