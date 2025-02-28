import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { ThemeProvider } from '@/components/theme-provider';
import Layout from '@/components/layout';
import Dashboard from './pages/dashboard';
import StudyActivities from './pages/study-activities/index';
import StudyActivity from './pages/study-activities/show';
import Words from './pages/words/index';
import Word from './pages/words/show';
import Groups from './pages/groups/index';
import Group from './pages/groups/show';
import Sessions from './pages/sessions/index';
import Settings from './pages/settings/index';

function App() {
  return (
    <ThemeProvider defaultTheme="light" storageKey="vite-ui-theme">
      <Router>
        <Layout>
          <Routes>
            <Route path="/" element={<Navigate to="/dashboard" replace />} />
            <Route path="/dashboard" element={<Dashboard />} />
            <Route path="/study-activities" element={<StudyActivities />} />
            <Route path="/study-activities/:id" element={<StudyActivity />} />
            <Route path="/words" element={<Words />} />
            <Route path="/words/:id" element={<Word />} />
            <Route path="/groups" element={<Groups />} />
            <Route path="/groups/:id" element={<Group />} />
            <Route path="/sessions" element={<Sessions />} />
            <Route path="/settings" element={<Settings />} />
          </Routes>
        </Layout>
      </Router>
    </ThemeProvider>
  );
}

export default App;