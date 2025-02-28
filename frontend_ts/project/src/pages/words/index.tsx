import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { ArrowDown, ArrowUp, Volume2 } from "lucide-react";

type SortDirection = 'asc' | 'desc';
type SortField = 'japanese' | 'romaji' | 'english' | 'correct' | 'wrong';

const mockWords = [
  {
    id: "1",
    japanese: "始める",
    romaji: "hajimeru",
    english: "to begin",
    correct: 15,
    wrong: 3
  },
  {
    id: "2",
    japanese: "食べる",
    romaji: "taberu",
    english: "to eat",
    correct: 25,
    wrong: 2
  },
  {
    id: "3",
    japanese: "飲む",
    romaji: "nomu",
    english: "to drink",
    correct: 18,
    wrong: 4
  },
  {
    id: "4",
    japanese: "見る",
    romaji: "miru",
    english: "to see",
    correct: 30,
    wrong: 1
  },
  {
    id: "5",
    japanese: "聞く",
    romaji: "kiku",
    english: "to listen/hear",
    correct: 22,
    wrong: 5
  },
  {
    id: "6",
    japanese: "行く",
    romaji: "iku",
    english: "to go",
    correct: 28,
    wrong: 2
  },
  {
    id: "7",
    japanese: "来る",
    romaji: "kuru",
    english: "to come",
    correct: 20,
    wrong: 6
  },
  {
    id: "8",
    japanese: "寝る",
    romaji: "neru",
    english: "to sleep",
    correct: 17,
    wrong: 4
  },
  {
    id: "9",
    japanese: "起きる",
    romaji: "okiru",
    english: "to wake up",
    correct: 19,
    wrong: 3
  },
  {
    id: "10",
    japanese: "話す",
    romaji: "hanasu",
    english: "to speak",
    correct: 24,
    wrong: 2
  }
];

export default function Words() {
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
    <div>
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
            {mockWords.map((word) => (
              <tr key={word.id} className="border-b">
                <td className="p-4">
                  <div className="flex items-center gap-1">
                    <a href={`/words/${word.id}`} className="text-primary hover:underline">
                      {word.japanese}
                    </a>
                    <button className="text-muted-foreground hover:text-primary transition-colors p-1 rounded-md">
                      <Volume2 className="h-4 w-4" />
                    </button>
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

      <div className="flex items-center justify-center gap-2 mt-4">
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