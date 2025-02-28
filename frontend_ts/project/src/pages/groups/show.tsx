import { useParams } from 'react-router-dom';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { ArrowDown, ArrowUp, Volume2 } from "lucide-react";
import { useState } from 'react';

type SortDirection = 'asc' | 'desc';
type SortField = 'japanese' | 'romaji' | 'english' | 'correct' | 'wrong';

const mockGroup = {
  id: "1",
  name: "Core Verbs",
  description: "Essential Japanese verbs for daily conversation",
  words: [
    {
      id: "1",
      japanese: "始める",
      romaji: "hajimeru",
      english: "to begin",
      correct: 15,
      wrong: 3
    }
  ]
};

export default function Group() {
  const { id } = useParams();
  const [sortField, setSortField] = useState<SortField>('japanese');
  const [sortDirection, setSortDirection] = useState<SortDirection>('asc');
  const [currentPage, setCurrentPage] = useState(1);
  const totalPages = 3;

  const handleSort = (field: SortField) => {
    if (field === sortField) {
      setSortDirection(sortDirection === 'asc' ? 'desc' : 'asc');
    } else {
      setSortField(field);
      setSortDirection('asc');
    }
  };

  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{mockGroup.name}</CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-muted-foreground">{mockGroup.description}</p>
        </CardContent>
      </Card>

      <div className="rounded-md border">
        <table className="w-full">
          <thead>
            <tr className="border-b bg-muted/50">
              {(['japanese', 'romaji', 'english', 'correct', 'wrong'] as const).map((field) => (
                <th
                  key={field}
                  className="p-4 text-left font-medium cursor-pointer hover:bg-muted/80"
                  onClick={() => handleSort(field)}
                >
                  <div className="flex items-center gap-2">
                    {field.charAt(0).toUpperCase() + field.slice(1)}
                    {sortField === field && (
                      sortDirection === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {mockGroup.words.map((word) => (
              <tr key={word.id} className="border-b">
                <td className="p-4">
                  <div className="flex items-center gap-2">
                    <a href={`/words/${word.id}`} className="text-primary hover:underline">
                      {word.japanese}
                    </a>
                    <Button variant="ghost" size="icon" className="h-6 w-6">
                      <Volume2 className="h-4 w-4" />
                    </Button>
                  </div>
                </td>
                <td className="p-4">{word.romaji}</td>
                <td className="p-4">{word.english}</td>
                <td className="p-4">{word.correct}</td>
                <td className="p-4">{word.wrong}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="flex items-center justify-center gap-2">
        <Button
          variant="outline"
          onClick={() => setCurrentPage(p => Math.max(1, p - 1))}
          disabled={currentPage === 1}
        >
          Previous
        </Button>
        <span className="text-sm">
          Page <strong>{currentPage}</strong> of {totalPages}
        </span>
        <Button
          variant="outline"
          onClick={() => setCurrentPage(p => Math.min(totalPages, p + 1))}
          disabled={currentPage === totalPages}
        >
          Next
        </Button>
      </div>
    </div>
  );
}