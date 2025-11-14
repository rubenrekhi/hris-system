import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { darkTheme } from './theme/darkTheme';
import Layout from './components/layout/Layout';

// Import pages
import HomePage from './pages/HomePage';
import EmployeeDirectoryPage from './pages/EmployeeDirectoryPage';
import OrgChartPage from './pages/OrgChartPage';
import AuditsPage from './pages/AuditsPage';
import TeamsPage from './pages/TeamsPage';
import ReportsPage from './pages/ReportsPage';
import ManagementPage from './pages/ManagementPage';

/**
 * Main App component with routing and theme configuration.
 */
function App() {
  return (
    <ThemeProvider theme={darkTheme}>
      <CssBaseline />
      <BrowserRouter>
        <Layout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/employees" element={<EmployeeDirectoryPage />} />
            <Route path="/org-chart" element={<OrgChartPage />} />
            <Route path="/audits" element={<AuditsPage />} />
            <Route path="/teams" element={<TeamsPage />} />
            <Route path="/reports" element={<ReportsPage />} />
            <Route path="/management" element={<ManagementPage />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
