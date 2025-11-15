import { useState, useEffect } from 'react';
import {
  Box,
  Typography,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TablePagination,
  TextField,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  CircularProgress,
  Alert,
  Collapse,
  IconButton,
  Chip,
} from '@mui/material';
import FilterListIcon from '@mui/icons-material/FilterList';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import { auditLogService } from '@/services';
import { cache } from '@/utils/cache';
import { formatDateTime, formatStatus } from '@/utils/formatters';
import DetailModal from '@/components/common/DetailModal';
import AuditLogDetail from '@/components/audits/AuditLogDetail';

export default function AuditsPage() {
  // Audit logs data
  const [auditLogs, setAuditLogs] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Pagination
  const [page, setPage] = useState(0);
  const [rowsPerPage, setRowsPerPage] = useState(25);

  // Filters
  const [entityTypeFilter, setEntityTypeFilter] = useState('');
  const [changeTypeFilter, setChangeTypeFilter] = useState('');
  const [entityIdFilter, setEntityIdFilter] = useState('');
  const [userIdFilter, setUserIdFilter] = useState('');
  const [dateFromFilter, setDateFromFilter] = useState('');
  const [dateToFilter, setDateToFilter] = useState('');
  const [filtersOpen, setFiltersOpen] = useState(true);

  // Modal state
  const [selectedAuditLogId, setSelectedAuditLogId] = useState(null);

  // Load audit logs with debouncing for filters
  useEffect(() => {
    // Only debounce when user is actively filtering with text inputs
    // Skip debounce for initial load and dropdown filter changes (instant feedback)
    const shouldDebounce =
      entityIdFilter.trim().length > 0 || userIdFilter.trim().length > 0;

    if (shouldDebounce) {
      const timer = setTimeout(() => {
        loadAuditLogs();
      }, 300); // 300ms debounce for text input filters
      return () => clearTimeout(timer);
    } else {
      // No debounce for initial load or dropdown filters
      loadAuditLogs();
    }
  }, [page, rowsPerPage, entityTypeFilter, changeTypeFilter, entityIdFilter, userIdFilter, dateFromFilter, dateToFilter]);

  const loadAuditLogs = async () => {
    // Check if we can use cached data for first page with no filters
    const isFirstPageNoFilters =
      page === 0 &&
      rowsPerPage === 25 &&
      !entityTypeFilter &&
      !changeTypeFilter &&
      !entityIdFilter.trim() &&
      !userIdFilter.trim() &&
      !dateFromFilter &&
      !dateToFilter;

    if (isFirstPageNoFilters) {
      const cachedAuditLogs = cache.get('audit_logs_page_0');
      if (cachedAuditLogs) {
        // Use cached data instantly, no loading state
        setAuditLogs(cachedAuditLogs.items || []);
        setTotal(cachedAuditLogs.total || 0);
        return;
      }
    }

    // Fetch from API
    setLoading(true);
    setError(null);

    try {
      const params = {
        limit: rowsPerPage,
        offset: page * rowsPerPage,
        order: 'desc', // Newest first
      };

      // Add filters only if they have values
      if (entityTypeFilter) {
        params.entity_type = entityTypeFilter;
      }
      if (changeTypeFilter) {
        params.change_type = changeTypeFilter;
      }
      if (entityIdFilter.trim()) {
        params.entity_id = entityIdFilter.trim();
      }
      if (userIdFilter.trim()) {
        params.changed_by_user_id = userIdFilter.trim();
      }
      if (dateFromFilter) {
        params.date_from = dateFromFilter;
      }
      if (dateToFilter) {
        params.date_to = dateToFilter;
      }

      const data = await auditLogService.listAuditLogs(params);
      setAuditLogs(data.items || []);
      setTotal(data.total || 0);

      // Cache first page with no filters
      if (isFirstPageNoFilters) {
        cache.set('audit_logs_page_0', data);
      }
    } catch (err) {
      setError(err.message);
      setAuditLogs([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  const handleChangePage = (event, newPage) => {
    setPage(newPage);
  };

  const handleChangeRowsPerPage = (event) => {
    setRowsPerPage(parseInt(event.target.value, 10));
    setPage(0); // Reset to first page
  };

  const handleClearFilters = () => {
    setEntityTypeFilter('');
    setChangeTypeFilter('');
    setEntityIdFilter('');
    setUserIdFilter('');
    setDateFromFilter('');
    setDateToFilter('');
    setPage(0);
  };

  // Helper to get change type color
  const getChangeTypeColor = (changeType) => {
    switch (changeType) {
      case 'CREATE':
        return 'success';
      case 'UPDATE':
        return 'info';
      case 'DELETE':
        return 'error';
      case 'BULK_UPDATE':
        return 'warning';
      default:
        return 'default';
    }
  };

  // Helper to get entity type color
  const getEntityTypeColor = (entityType) => {
    switch (entityType) {
      case 'EMPLOYEE':
        return 'primary';
      case 'DEPARTMENT':
        return 'secondary';
      case 'TEAM':
        return 'info';
      case 'USER':
        return 'warning';
      default:
        return 'default';
    }
  };

  // Helper to truncate UUID
  const truncateUuid = (uuid) => {
    if (!uuid) return '—';
    return `${uuid.slice(0, 8)}...`;
  };

  // Count active filters
  const activeFilterCount =
    (entityTypeFilter ? 1 : 0) +
    (changeTypeFilter ? 1 : 0) +
    (entityIdFilter.trim() ? 1 : 0) +
    (userIdFilter.trim() ? 1 : 0) +
    (dateFromFilter ? 1 : 0) +
    (dateToFilter ? 1 : 0);

  return (
    <Box sx={{ px: 3, py: 2 }}>
      {/* Page Title */}
      <Typography variant="h3" component="h1" gutterBottom sx={{ mb: 3 }}>
        Audit Logs
      </Typography>

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
              {/* Entity Type Filter */}
              <FormControl fullWidth>
                <InputLabel>Entity Type</InputLabel>
                <Select
                  value={entityTypeFilter}
                  onChange={(e) => setEntityTypeFilter(e.target.value)}
                  label="Entity Type"
                >
                  <MenuItem value="">
                    <em>All</em>
                  </MenuItem>
                  <MenuItem value="EMPLOYEE">Employee</MenuItem>
                  <MenuItem value="DEPARTMENT">Department</MenuItem>
                  <MenuItem value="TEAM">Team</MenuItem>
                  <MenuItem value="USER">User</MenuItem>
                </Select>
              </FormControl>

              {/* Change Type Filter */}
              <FormControl fullWidth>
                <InputLabel>Change Type</InputLabel>
                <Select
                  value={changeTypeFilter}
                  onChange={(e) => setChangeTypeFilter(e.target.value)}
                  label="Change Type"
                >
                  <MenuItem value="">
                    <em>All</em>
                  </MenuItem>
                  <MenuItem value="CREATE">Create</MenuItem>
                  <MenuItem value="UPDATE">Update</MenuItem>
                  <MenuItem value="DELETE">Delete</MenuItem>
                  <MenuItem value="BULK_UPDATE">Bulk Update</MenuItem>
                </Select>
              </FormControl>

              {/* Entity ID Filter */}
              <TextField
                fullWidth
                label="Entity ID"
                placeholder="UUID"
                value={entityIdFilter}
                onChange={(e) => setEntityIdFilter(e.target.value)}
              />

              {/* User ID Filter */}
              <TextField
                fullWidth
                label="Changed By User ID"
                placeholder="UUID"
                value={userIdFilter}
                onChange={(e) => setUserIdFilter(e.target.value)}
              />

              {/* Date From Filter */}
              <TextField
                fullWidth
                type="date"
                label="Date From"
                value={dateFromFilter}
                onChange={(e) => setDateFromFilter(e.target.value)}
                InputLabelProps={{ shrink: true }}
              />

              {/* Date To Filter */}
              <TextField
                fullWidth
                type="date"
                label="Date To"
                value={dateToFilter}
                onChange={(e) => setDateToFilter(e.target.value)}
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

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Audit Logs Table */}
      <Paper sx={{ backgroundColor: 'background.paper' }}>
        <TableContainer>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>Timestamp</TableCell>
                <TableCell>Entity Type</TableCell>
                <TableCell>Change Type</TableCell>
                <TableCell>Entity ID</TableCell>
                <TableCell>Changed By</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {/* Loading State */}
              {loading && (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                    <CircularProgress />
                  </TableCell>
                </TableRow>
              )}

              {/* Empty State */}
              {!loading && auditLogs.length === 0 && (
                <TableRow>
                  <TableCell colSpan={5} align="center" sx={{ py: 4 }}>
                    <Typography variant="body1" color="text.secondary">
                      No audit logs found
                    </Typography>
                  </TableCell>
                </TableRow>
              )}

              {/* Audit Log Rows */}
              {!loading &&
                auditLogs.map((log) => (
                  <TableRow
                    key={log.id}
                    hover
                    sx={{ cursor: 'pointer' }}
                    onClick={() => setSelectedAuditLogId(log.id)}
                  >
                    <TableCell>{formatDateTime(log.created_at)}</TableCell>
                    <TableCell>
                      <Chip
                        label={formatStatus(log.entity_type)}
                        size="small"
                        color={getEntityTypeColor(log.entity_type)}
                      />
                    </TableCell>
                    <TableCell>
                      <Chip
                        label={formatStatus(log.change_type)}
                        size="small"
                        color={getChangeTypeColor(log.change_type)}
                      />
                    </TableCell>
                    <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                      {truncateUuid(log.entity_id)}
                    </TableCell>
                    <TableCell sx={{ fontFamily: 'monospace', fontSize: '0.875rem' }}>
                      {log.changed_by_user_id ? truncateUuid(log.changed_by_user_id) : 'System'}
                    </TableCell>
                  </TableRow>
                ))}
            </TableBody>
          </Table>
        </TableContainer>

        {/* Pagination */}
        <TablePagination
          component="div"
          count={total}
          page={page}
          onPageChange={handleChangePage}
          rowsPerPage={rowsPerPage}
          onRowsPerPageChange={handleChangeRowsPerPage}
          rowsPerPageOptions={[10, 25, 50, 100]}
        />
      </Paper>

      {/* Detail Modal */}
      <DetailModal
        open={!!selectedAuditLogId}
        onClose={() => setSelectedAuditLogId(null)}
        title="Audit Log Details"
        maxWidth="lg"
      >
        <AuditLogDetail auditLogId={selectedAuditLogId} />
      </DetailModal>
    </Box>
  );
}
