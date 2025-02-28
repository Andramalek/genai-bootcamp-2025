import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { ArrowDown, ArrowUp } from "lucide-react";

type SortDirection = 'asc' | 'desc';
type SortField = 'name' | 'words';

const mockGroups = [
  {
    id: "1",
    name: "Core Verbs",
    wordCount: 150
  },
  {
    id: "2",
    name: "JLPT N5",
    wordCount: 800
  }
];

export default function Groups() {
  const [sortField, setSortField] = useState<SortField>('name');
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
              <th
                className="p-4 text-left font-medium cursor-pointer hover:bg-muted/80"
                onClick={() => handleSort('name')}
              >
                <div className="flex items-center gap-2">
                  Group Name
                  {sortField === 'name' && (
                    sortDirection === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />
                  )}
                </div>
              </th>
              <th
                className="p-4 text-left font-medium cursor-pointer hover:bg-muted/80"
                onClick={() => handleSort('words')}
              >
                <div className="flex items-center gap-2">
                  Words
                  {sortField === 'words' && (
                    sortDirection === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />
                  )}
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            {mockGroups.map((group) => (
              <tr key={group.id} className="border-b">
                <td className="p-4">
                  <a href={`/groups/${group.id}`} className="text-primary hover:underline">
                    {group.name}
                  </a>
                </td>
                <td className="p-4">{group.wordCount}</td>
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