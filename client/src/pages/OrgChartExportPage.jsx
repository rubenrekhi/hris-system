import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  TextField,
  Collapse,
  IconButton,
  Chip,
  Alert,
  CircularProgress,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import FilterListIcon from '@mui/icons-material/FilterList';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import DownloadIcon from '@mui/icons-material/Download';
import DescriptionIcon from '@mui/icons-material/Description';
import TableChartIcon from '@mui/icons-material/TableChart';
import PictureAsPdfIcon from '@mui/icons-material/PictureAsPdf';
import { exportService, departmentService, teamService } from '@/services';

export default function OrgChartExportPage() {
  const navigate = useNavigate();

  // Filter state
  const [departmentFilter, setDepartmentFilter] = useState('');
  const [teamFilter, setTeamFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [hiredFromFilter, setHiredFromFilter] = useState('');
  const [hiredToFilter, setHiredToFilter] = useState('');
  const [filtersOpen, setFiltersOpen] = useState(true);

  // Filter options
  const [departments, setDepartments] = useState([]);
  const [teams, setTeams] = useState([]);
  const [departmentsLoading, setDepartmentsLoading] = useState(false);
  const [teamsLoading, setTeamsLoading] = useState(false);

  // Export state
  const [exportingCSV, setExportingCSV] = useState(false);
  const [exportingExcel, setExportingExcel] = useState(false);
  const [exportingPDF, setExportingPDF] = useState(false);
  const [error, setError] = useState(null);

  // Load departments and teams for filter dropdowns
  useEffect(() => {
    const loadFilterOptions = async () => {
      // Load departments
      setDepartmentsLoading(true);
      try {
        const deptData = await departmentService.listDepartments({ limit: 100 });
        setDepartments(deptData.items || []);
      } catch (err) {
        console.error('Failed to load departments:', err);
      } finally {
        setDepartmentsLoading(false);
      }

      // Load teams
      setTeamsLoading(true);
      try {
        const teamData = await teamService.listTeams({ limit: 100 });
        setTeams(teamData.items || []);
      } catch (err) {
        console.error('Failed to load teams:', err);
      } finally {
        setTeamsLoading(false);
      }
    };

    loadFilterOptions();
  }, []);

  // Build filter object for API
  const buildFilters = () => {
    const filters = {};
    if (departmentFilter) filters.department_id = departmentFilter;
    if (teamFilter) filters.team_id = teamFilter;
    if (statusFilter) filters.status = statusFilter;
    if (hiredFromFilter) filters.hired_from = hiredFromFilter;
    if (hiredToFilter) filters.hired_to = hiredToFilter;
    return filters;
  };

  // Handle export actions
  const handleExport = async (format) => {
    setError(null);
    const filters = buildFilters();

    try {
      let blob;
      let filename;

      if (format === 'csv') {
        setExportingCSV(true);
        blob = await exportService.exportOrgChartCSV(filters);
        filename = `org-chart-${new Date().toISOString().split('T')[0]}.csv`;
      } else if (format === 'excel') {
        setExportingExcel(true);
        blob = await exportService.exportOrgChartExcel(filters);
        filename = `org-chart-${new Date().toISOString().split('T')[0]}.xlsx`;
      } else if (format === 'pdf') {
        setExportingPDF(true);
        blob = await exportService.exportOrgChartPDF(filters);
        filename = `org-chart-${new Date().toISOString().split('T')[0]}.pdf`;
      }

      exportService.downloadFile(blob, filename);
    } catch (err) {
      console.error(`Failed to export as ${format}:`, err);
      setError(`Failed to export organization chart. Please try again.`);
    } finally {
      setExportingCSV(false);
      setExportingExcel(false);
      setExportingPDF(false);
    }
  };

  const handleClearFilters = () => {
    setDepartmentFilter('');
    setTeamFilter('');
    setStatusFilter('');
    setHiredFromFilter('');
    setHiredToFilter('');
  };

  // Count active filters
  const activeFilterCount =
    (departmentFilter ? 1 : 0) +
    (teamFilter ? 1 : 0) +
    (statusFilter ? 1 : 0) +
    (hiredFromFilter ? 1 : 0) +
    (hiredToFilter ? 1 : 0);

  return (
    <Box sx={{ px: 3, py: 2 }}>
      {/* Back Button and Title */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton onClick={() => navigate('/reports')} sx={{ color: 'primary.main' }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h3" component="h1">
          Export Organization Chart
        </Typography>
      </Box>

      <Typography variant="body1" sx={{ mb: 4, color: 'text.secondary' }}>
        Export hierarchical organizational structure with reporting relationships
      </Typography>

      {/* Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Filters Panel */}
      <Paper sx={{ mb: 3, backgroundColor: 'background.paper' }}>
        {/* Filter Header */}
        <Box
          sx={{
            px: 2,
            py: 1.5,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            cursor: 'pointer',
            backgroundColor: 'rgba(144, 202, 249, 0.08)',
          }}
          onClick={() => setFiltersOpen(!filtersOpen)}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <FilterListIcon />
            <Typography variant="h6">Filters</Typography>
            {activeFilterCount > 0 && (
              <Chip label={activeFilterCount} size="small" color="primary" sx={{ ml: 1 }} />
            )}
          </Box>
          <IconButton size="small">
            {filtersOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>

        {/* Filter Controls */}
        <Collapse in={filtersOpen}>
          <Box sx={{ p: 2 }}>
            <Box
              sx={{
                display: 'grid',
                gridTemplateColumns: {
                  xs: '1fr',
                  sm: 'repeat(2, 1fr)',
                  md: 'repeat(3, 1fr)',
                },
                gap: 2,
              }}
            >
              {/* Department Filter */}
              <FormControl fullWidth>
                <InputLabel>Department</InputLabel>
                <Select
                  value={departmentFilter}
                  onChange={(e) => setDepartmentFilter(e.target.value)}
                  label="Department"
                  disabled={departmentsLoading}
                >
                  <MenuItem value="">
                    <em>All</em>
                  </MenuItem>
                  {departments.map((dept) => (
                    <MenuItem key={dept.id} value={dept.id}>
                      {dept.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Team Filter */}
              <FormControl fullWidth>
                <InputLabel>Team</InputLabel>
                <Select
                  value={teamFilter}
                  onChange={(e) => setTeamFilter(e.target.value)}
                  label="Team"
                  disabled={teamsLoading}
                >
                  <MenuItem value="">
                    <em>All</em>
                  </MenuItem>
                  {teams.map((team) => (
                    <MenuItem key={team.id} value={team.id}>
                      {team.name}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>

              {/* Status Filter */}
              <FormControl fullWidth>
                <InputLabel>Status</InputLabel>
                <Select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  label="Status"
                >
                  <MenuItem value="">
                    <em>All</em>
                  </MenuItem>
                  <MenuItem value="ACTIVE">Active</MenuItem>
                  <MenuItem value="ON_LEAVE">On Leave</MenuItem>
                </Select>
              </FormControl>

              {/* Hired From Date */}
              <TextField
                fullWidth
                type="date"
                label="Hired From"
                value={hiredFromFilter}
                onChange={(e) => setHiredFromFilter(e.target.value)}
                InputLabelProps={{ shrink: true }}
              />

              {/* Hired To Date */}
              <TextField
                fullWidth
                type="date"
                label="Hired To"
                value={hiredToFilter}
                onChange={(e) => setHiredToFilter(e.target.value)}
                InputLabelProps={{ shrink: true }}
              />
            </Box>

            {/* Clear Filters Button */}
            {activeFilterCount > 0 && (
              <Box sx={{ mt: 2, display: 'flex', justifyContent: 'flex-end' }}>
                <Typography
                  variant="body2"
                  sx={{
                    color: 'primary.main',
                    cursor: 'pointer',
                    '&:hover': { textDecoration: 'underline' },
                  }}
                  onClick={handleClearFilters}
                >
                  Clear all filters
                </Typography>
              </Box>
            )}
          </Box>
        </Collapse>
      </Paper>

      {/* Export Section */}
      <Paper sx={{ p: 3, backgroundColor: 'background.paper' }}>
        <Typography variant="h6" gutterBottom sx={{ mb: 3 }}>
          Select Export Format
        </Typography>

        <Box
          sx={{
            display: 'grid',
            gridTemplateColumns: {
              xs: '1fr',
              sm: 'repeat(3, 1fr)',
            },
            gap: 2,
          }}
        >
          {/* CSV Export */}
          <Button
            variant="contained"
            size="large"
            startIcon={exportingCSV ? <CircularProgress size={20} /> : <DescriptionIcon />}
            onClick={() => handleExport('csv')}
            disabled={exportingCSV || exportingExcel || exportingPDF}
            sx={{ py: 2 }}
          >
            {exportingCSV ? 'Exporting...' : 'Export as CSV'}
          </Button>

          {/* Excel Export */}
          <Button
            variant="contained"
            size="large"
            startIcon={exportingExcel ? <CircularProgress size={20} /> : <TableChartIcon />}
            onClick={() => handleExport('excel')}
            disabled={exportingCSV || exportingExcel || exportingPDF}
            sx={{ py: 2 }}
          >
            {exportingExcel ? 'Exporting...' : 'Export as Excel'}
          </Button>

          {/* PDF Export */}
          <Button
            variant="contained"
            size="large"
            startIcon={exportingPDF ? <CircularProgress size={20} /> : <PictureAsPdfIcon />}
            onClick={() => handleExport('pdf')}
            disabled={exportingCSV || exportingExcel || exportingPDF}
            sx={{ py: 2 }}
          >
            {exportingPDF ? 'Exporting...' : 'Export as PDF'}
          </Button>
        </Box>

        <Typography variant="body2" sx={{ mt: 3, color: 'text.secondary' }}>
          The file will be downloaded to your default downloads folder. Applied filters will be
          reflected in the exported data.
        </Typography>
      </Paper>
    </Box>
  );
}
