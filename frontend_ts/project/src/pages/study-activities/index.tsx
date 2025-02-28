import { Card, CardContent, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ExternalLink, Eye } from "lucide-react";

const activities = [
  {
    id: "1",
    title: "Adventure MUD",
    thumbnail: "https://images.unsplash.com/photo-1526481280693-3bfa7568e0f3?w=800&auto=format&fit=crop",
    description: "Learn Japanese through text-based adventure games"
  },
  {
    id: "2",
    title: "Typing Tutor",
    thumbnail: "https://images.unsplash.com/photo-1515378791036-0648a3ef77b2?w=800&auto=format&fit=crop",
    description: "Practice typing Japanese characters"
  }
];

export default function StudyActivities() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
      {activities.map((activity) => (
        <Card key={activity.id}>
          <CardHeader>
            <img
              src={activity.thumbnail}
              alt={activity.title}
              className="w-full h-48 object-cover rounded-t-lg"
            />
            <CardTitle className="mt-4">{activity.title}</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-muted-foreground">{activity.description}</p>
          </CardContent>
          <CardFooter className="flex gap-2">
            <Button
              variant="destructive"
              onClick={() => window.open(`http://localhost:8081?group_id=${activity.id}`, '_blank')}
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Launch
            </Button>
            <Button variant="outline" asChild>
              <a href={`/study-activities/${activity.id}`}>
                <Eye className="h-4 w-4 mr-2" />
                View
              </a>
            </Button>
          </CardFooter>
        </Card>
      ))}
    </div>
  );
}