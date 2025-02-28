import { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { ArrowRightIcon, BarChart3Icon, BookIcon, CheckCircleIcon, ClockIcon } from 'lucide-react';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Progress } from '@/components/ui/progress';
import { dashboardAPI } from '@/services/api';

interface LastStudySession {
  id: number;
  group_id: number;
  created_at: string;
  study_activity_id: number;
  group_name: string;
}

interface StudyProgress {
  total_words_studied: number;
  total_available_words: number;
}

interface QuickStats {
  total_words: number;
  total_groups: number;
  words_mastered: number;
  recent_accuracy: number;
}

export default function Dashboard() {
  const [lastSession, setLastSession] = useState<LastStudySession | null>(null);
  const [progress, setProgress] = useState<StudyProgress | null>(null);
  const [stats, setStats] = useState<QuickStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchDashboardData() {
      try {
        setLoading(true);
        const [lastSessionData, progressData, statsData] = await Promise.all([
          dashboardAPI.getLastStudySession(),
          dashboardAPI.getStudyProgress(),
          dashboardAPI.getQuickStats(),
        ]);

        setLastSession(lastSessionData);
        setProgress(progressData);
        setStats(statsData);
        setError(null);
      } catch (err) {
        console.error('Failed to fetch dashboard data:', err);
        setError('Failed to load dashboard data. Please try again later.');
      } finally {
        setLoading(false);
      }
    }

    fetchDashboardData();
  }, []);

  if (loading) {
    return <div className="flex items-center justify-center h-96">Loading dashboard data...</div>;
  }

  if (error) {
    return (
      <Card className="border-destructive">
        <CardHeader>
          <CardTitle className="text-destructive">Error</CardTitle>
        </CardHeader>
        <CardContent>
          <p>{error}</p>
        </CardContent>
        <CardFooter>
          <Button onClick={() => window.location.reload()}>Try Again</Button>
        </CardFooter>
      </Card>
    );
  }

  // Calculate mastery percentage from the available data
  const masteryPercentage = progress 
    ? Math.round((progress.total_words_studied / progress.total_available_words) * 100) || 0
    : 0;

  return (
    <div className="space-y-8">
      <h1 className="text-3xl font-bold">Dashboard</h1>
      
      {/* Last Study Session */}
      <Card>
        <CardHeader>
          <CardTitle>Last Study Session</CardTitle>
          <CardDescription>
            Your most recent learning activity
          </CardDescription>
        </CardHeader>
        <CardContent>
          {lastSession && lastSession.id ? (
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <h3 className="text-xl font-medium">Activity #{lastSession.study_activity_id}</h3>
                  <p className="text-sm text-muted-foreground">
                    <ClockIcon className="inline mr-1 h-4 w-4" />
                    {new Date(lastSession.created_at).toLocaleDateString('en-US', {
                      year: 'numeric',
                      month: 'long',
                      day: 'numeric',
                      hour: '2-digit',
                      minute: '2-digit',
                    })}
                  </p>
                </div>
                <Link to={`/groups/${lastSession.group_id}`}>
                  <Button variant="outline" size="sm">
                    View Group
                  </Button>
                </Link>
              </div>
              <div>
                <h4 className="font-medium mb-1">Group:</h4>
                <p>{lastSession.group_name}</p>
              </div>
            </div>
          ) : (
            <p className="text-muted-foreground">No study sessions found. Start studying to see your activity here!</p>
          )}
        </CardContent>
        <CardFooter>
          <Link to={`/study-activities`} className="w-full">
            <Button className="w-full">
              Start Studying <ArrowRightIcon className="ml-2 h-4 w-4" />
            </Button>
          </Link>
        </CardFooter>
      </Card>

      {/* Study Progress */}
      <Card>
        <CardHeader>
          <CardTitle>Study Progress</CardTitle>
          <CardDescription>
            Track your vocabulary mastery
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm font-medium">Words Studied</span>
              <span className="text-sm text-muted-foreground">
                {progress?.total_words_studied || 0}/{progress?.total_available_words || 0}
              </span>
            </div>
            <Progress value={masteryPercentage} />
          </div>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span className="text-sm font-medium">Mastery</span>
              <span className="text-sm text-muted-foreground">{masteryPercentage}%</span>
            </div>
            <div className="flex items-center gap-2">
              <BookIcon className="h-4 w-4 text-muted-foreground" />
              <div className="text-sm text-muted-foreground">
                Keep practicing to improve your mastery!
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Quick Stats */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Success Rate</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center">
              <CheckCircleIcon className="mr-2 h-4 w-4 text-green-500" />
              <span className="text-2xl font-bold">
                {stats?.recent_accuracy ? Math.round(stats.recent_accuracy) : 0}%
              </span>
            </div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Total Words</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_words || 0}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Active Groups</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats?.total_groups || 0}</div>
          </CardContent>
        </Card>
        
        <Card>
          <CardHeader className="pb-2">
            <CardTitle className="text-sm font-medium">Words Mastered</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center">
              <BarChart3Icon className="mr-2 h-4 w-4 text-blue-500" />
              <span className="text-2xl font-bold">{stats?.words_mastered || 0}</span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}