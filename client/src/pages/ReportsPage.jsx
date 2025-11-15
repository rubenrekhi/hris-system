import { Box, Typography, Paper, Grid } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import BusinessIcon from '@mui/icons-material/Business';
import AccountTreeIcon from '@mui/icons-material/AccountTree';

export default function ReportsPage() {
  const navigate = useNavigate();

  const exportOptions = [
    {
      title: 'Employee Directory Export',
      description: 'Export a flat list of all employees with their details',
      icon: BusinessIcon,
      path: '/reports/directory',
      color: '#90caf9',
    },
    {
      title: 'Organization Chart Export',
      description: 'Export hierarchical organizational structure with reporting relationships',
      icon: AccountTreeIcon,
      path: '/reports/org-chart',
      color: '#f48fb1',
    },
  ];

  return (
    <Box sx={{ px: 3, py: 2 }}>
      <Typography variant="h3" component="h1" gutterBottom sx={{ mb: 4 }}>
        Reports & Exports
      </Typography>

      <Typography variant="body1" sx={{ mb: 4, color: 'text.secondary' }}>
        Select an export type to configure filters and download your data
      </Typography>

      <Box sx={{ maxWidth: 800, mx: 'auto', display: 'flex', flexDirection: 'column', gap: 3 }}>
        {exportOptions.map((option) => {
          const IconComponent = option.icon;
          return (
            <Paper
              key={option.path}
              sx={{
                p: 3,
                cursor: 'pointer',
                transition: 'all 0.2s ease-in-out',
                backgroundColor: 'background.paper',
                minHeight: 120,
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: `0 8px 24px ${option.color}33`,
                },
              }}
              onClick={() => navigate(option.path)}
            >
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                <Box
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    backgroundColor: `${option.color}20`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  <IconComponent sx={{ fontSize: 40, color: option.color }} />
                </Box>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
                    {option.title}
                  </Typography>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    {option.description}
                  </Typography>
                </Box>
              </Box>
            </Paper>
          );
        })}
      </Box>
    </Box>
  );
}
