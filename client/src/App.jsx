import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { ThemeProvider } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { darkTheme } from './theme/darkTheme';
import Layout from './components/layout/Layout';
import ProtectedRoute from './components/ProtectedRoute';

// Import pages
import Login from './pages/Login';
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
        <Routes>
          {/* Public route - Login */}
          <Route path="/login" element={<Login />} />

          {/* Protected routes - require authentication */}
          <Route
            path="/*"
            element={
              <ProtectedRoute>
                <Layout>
                  <Routes>
                    <Route path="/" element={<HomePage />} />
                    <Route path="/dashboard" element={<HomePage />} />
                    <Route path="/employees" element={<EmployeeDirectoryPage />} />
                    <Route path="/org-chart" element={<OrgChartPage />} />
                    <Route path="/audits" element={<AuditsPage />} />
                    <Route path="/teams" element={<TeamsPage />} />
                    <Route path="/reports" element={<ReportsPage />} />
                    <Route path="/reports/directory" element={<DirectoryExportPage />} />
                    <Route path="/reports/org-chart" element={<OrgChartExportPage />} />

                    {/* Management routes - require hr role or higher (hr and admin can access) */}
                    <Route
                      path="/management"
                      element={
                        <ProtectedRoute minimumRole="hr">
                          <ManagementPage />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/management/bulk-import"
                      element={
                        <ProtectedRoute minimumRole="hr">
                          <BulkImportPage />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/management/create-employee"
                      element={
                        <ProtectedRoute minimumRole="hr">
                          <CreateEmployeePage />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/management/promote-ceo"
                      element={
                        <ProtectedRoute minimumRole="admin">
                          <PromoteToCEOPage />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/management/replace-ceo"
                      element={
                        <ProtectedRoute minimumRole="admin">
                          <ReplaceCEOPage />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/management/create-team"
                      element={
                        <ProtectedRoute minimumRole="hr">
                          <CreateTeamPage />
                        </ProtectedRoute>
                      }
                    />
                    <Route
                      path="/management/create-department"
                      element={
                        <ProtectedRoute minimumRole="hr">
                          <CreateDepartmentPage />
                        </ProtectedRoute>
                      }
                    />
                  </Routes>
                </Layout>
              </ProtectedRoute>
            }
          />
        </Routes>
      </BrowserRouter>
    </ThemeProvider>
  );
}

export default App;
