import { Box, Card, CardContent, Typography, Chip } from '@mui/material';
import PersonIcon from '@mui/icons-material/Person';

/**
 * Custom node component for displaying an employee in the org chart.
 * Shows employee name, title, status, and department.
 *
 * @param {Object} employee - Employee data
 * @param {Function} onClick - Handler for clicking the node
 */
export default function OrgChartNode({ employee, onClick }) {
  if (!employee) return null;

  return (
    <Card
      variant="outlined"
      sx={{
        cursor: 'pointer',
        transition: 'all 0.2s',
        '&:hover': {
          boxShadow: 2,
          borderColor: 'primary.main',
        },
        minWidth: 280,
        maxWidth: 320,
      }}
      onClick={onClick}
    >
      <CardContent sx={{ pb: 2, '&:last-child': { pb: 2 } }}>
        {/* Employee Name */}
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 1 }}>
          <PersonIcon color="primary" fontSize="small" />
          <Typography variant="subtitle1" fontWeight={600}>
            {employee.name}
          </Typography>
        </Box>

        {/* Job Title */}
        {employee.title && (
          <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
            {employee.title}
          </Typography>
        )}

        {/* Department and Status Row */}
        <Box sx={{ display: 'flex', gap: 1, flexWrap: 'wrap', mt: 1.5 }}>
          {/* Department Badge */}
          {employee.department_name && (
            <Chip
              label={employee.department_name}
              size="small"
              variant="outlined"
              sx={{ fontSize: '0.7rem' }}
            />
          )}

          {/* Status Badge */}
          <Chip
            label={employee.status || 'ACTIVE'}
            size="small"
            color={employee.status === 'ACTIVE' ? 'success' : 'default'}
            sx={{ fontSize: '0.7rem' }}
          />
        </Box>
      </CardContent>
    </Card>
  );
}
