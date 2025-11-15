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
import DirectoryExportPage from './pages/DirectoryExportPage';
import OrgChartExportPage from './pages/OrgChartExportPage';
import ManagementPage from './pages/ManagementPage';
import BulkImportPage from './pages/BulkImportPage';
import CreateEmployeePage from './pages/CreateEmployeePage';
import PromoteToCEOPage from './pages/PromoteToCEOPage';
import ReplaceCEOPage from './pages/ReplaceCEOPage';
import CreateTeamPage from './pages/CreateTeamPage';
import CreateDepartmentPage from './pages/CreateDepartmentPage';

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
            <Route path="/reports/directory" element={<DirectoryExportPage />} />
            <Route path="/reports/org-chart" element={<OrgChartExportPage />} />
            <Route path="/management" element={<ManagementPage />} />
            <Route path="/management/bulk-import" element={<BulkImportPage />} />
            <Route path="/management/create-employee" element={<CreateEmployeePage />} />
            <Route path="/management/promote-ceo" element={<PromoteToCEOPage />} />
            <Route path="/management/replace-ceo" element={<ReplaceCEOPage />} />
            <Route path="/management/create-team" element={<CreateTeamPage />} />
            <Route path="/management/create-department" element={<CreateDepartmentPage />} />
          </Routes>
        </Layout>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
