import { useState } from 'react';
import { Button } from "@/components/ui/button";
import { ArrowDown, ArrowUp } from "lucide-react";

type SortDirection = 'asc' | 'desc';
type SortField = 'activity' | 'group' | 'startTime' | 'endTime' | 'reviewItems';

const mockSessions = [
  {
    id: "1",
    activity: "Adventure MUD",
    activityId: "1",
    group: "Core Verbs",
    groupId: "1",
    startTime: "2024-03-15 09:30 AM",
    endTime: "2024-03-15 10:15 AM",
    reviewItems: 25
  }
];

export default function Sessions() {
  const [sortField, setSortField] = useState<SortField>('startTime');
  const [sortDirection, setSortDirection] = useState<SortDirection>('desc');
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
                onClick={() => handleSort('activity')}
              >
                <div className="flex items-center gap-2">
                  Activity
                  {sortField === 'activity' && (
                    sortDirection === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />
                  )}
                </div>
              </th>
              <th
                className="p-4 text-left font-medium cursor-pointer hover:bg-muted/80"
                onClick={() => handleSort('group')}
              >
                <div className="flex items-center gap-2">
                  Group
                  {sortField === 'group' && (
                    sortDirection === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />
                  )}
                </div>
              </th>
              <th
                className="p-4 text-left font-medium cursor-pointer hover:bg-muted/80"
                onClick={() => handleSort('startTime')}
              >
                <div className="flex items-center gap-2">
                  Start Time
                  {sortField === 'startTime' && (
                    sortDirection === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />
                  )}
                </div>
              </th>
              <th
                className="p-4 text-left font-medium cursor-pointer hover:bg-muted/80"
                onClick={() => handleSort('endTime')}
              >
                <div className="flex items-center gap-2">
                  End Time
                  {sortField === 'endTime' && (
                    sortDirection === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />
                  )}
                </div>
              </th>
              <th
                className="p-4 text-left font-medium cursor-pointer hover:bg-muted/80"
                onClick={() => handleSort('reviewItems')}
              >
                <div className="flex items-center gap-2">
                  Review Items
                  {sortField === 'reviewItems' && (
                    sortDirection === 'asc' ? <ArrowUp className="h-4 w-4" /> : <ArrowDown className="h-4 w-4" />
                  )}
                </div>
              </th>
            </tr>
          </thead>
          <tbody>
            {mockSessions.map((session) => (
              <tr key={session.id} className="border-b">
                <td className="p-4">
                  <a href={`/study-activities/${session.activityId}`} className="text-primary hover:underline">
                    {session.activity}
                  </a>
                </td>
                <td className="p-4">
                  <a href={`/groups/${session.groupId}`} className="text-primary hover:underline">
                    {session.group}
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