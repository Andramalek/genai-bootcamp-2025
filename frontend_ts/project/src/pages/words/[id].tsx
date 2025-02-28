import { useParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Volume2 } from "lucide-react";

const mockWord = {
  id: "1",
  japanese: "始める",
  romaji: "hajimeru",
  english: "to begin",
  correct: 15,
  wrong: 3,
  groups: ["Core Verbs", "JLPT N5"],
  examples: [
    {
      japanese: "仕事を始める",
      romaji: "shigoto wo hajimeru",
      english: "to start work"
    }
  ]
};

export default function Word() {
  const { id } = useParams();

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <div className="flex items-center gap-4">
            <CardTitle className="text-3xl">{mockWord.japanese}</CardTitle>
            <Button variant="outline" size="icon">
              <Volume2 className="h-4 w-4" />
            </Button>
          </div>
        </CardHeader>
        <CardContent>
          <div className="grid gap-4">
            <div>
              <h3 className="font-semibold">Readings</h3>
              <p className="text-muted-foreground">{mockWord.romaji}</p>
            </div>
            <div>
              <h3 className="font-semibold">Meaning</h3>
              <p className="text-muted-foreground">{mockWord.english}</p>
            </div>
            <div>
              <h3 className="font-semibold">Groups</h3>
              <div className="flex gap-2 mt-1">
                {mockWord.groups.map((group) => (
                  <span key={group} className="bg-secondary text-secondary-foreground px-2 py-1 rounded-md text-sm">
                    {group}
                  </span>
                ))}
              </div>
            </div>
            <div>
              <h3 className="font-semibold">Study Progress</h3>
              <div className="grid grid-cols-2 gap-4 mt-1">
                <div className="bg-secondary p-4 rounded-md">
                  <div className="text-2xl font-bold">{mockWord.correct}</div>
                  <div className="text-sm text-muted-foreground">Correct</div>
                </div>
                <div className="bg-secondary p-4 rounded-md">
                  <div className="text-2xl font-bold">{mockWord.wrong}</div>
                  <div className="text-sm text-muted-foreground">Wrong</div>
                </div>
              </div>
            </div>
            <div>
              <h3 className="font-semibold">Example Sentences</h3>
              <div className="space-y-2 mt-1">
                {mockWord.examples.map((example, index) => (
                  <div key={index} className="bg-secondary p-4 rounded-md">
                    <div className="flex items-center gap-2">
                      <span>{example.japanese}</span>
                      <Button variant="ghost" size="icon" className="h-6 w-6">
                        <Volume2 className="h-4 w-4" />
                      </Button>
                    </div>
                    <div className="text-sm text-muted-foreground">{example.romaji}</div>
                    <div className="text-sm text-muted-foreground">{example.english}</div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}