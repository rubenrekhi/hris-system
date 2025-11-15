import { Box, Typography, Paper, Grid } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import UploadFileIcon from '@mui/icons-material/UploadFile';
import PersonAddIcon from '@mui/icons-material/PersonAdd';
import WorkspacePremiumIcon from '@mui/icons-material/WorkspacePremium';
import SwapHorizIcon from '@mui/icons-material/SwapHoriz';
import GroupsIcon from '@mui/icons-material/Groups';
import BusinessIcon from '@mui/icons-material/Business';

export default function ManagementPage() {
  const navigate = useNavigate();

  const managementTasks = [
    {
      title: 'Bulk Import Employees',
      description: 'Upload CSV or Excel file to import multiple employees at once',
      icon: UploadFileIcon,
      path: '/management/bulk-import',
      color: '#90caf9',
    },
    {
      title: 'Create New Employee',
      description: 'Add a new employee to the organization manually',
      icon: PersonAddIcon,
      path: '/management/create-employee',
      color: '#f48fb1',
    },
    {
      title: 'Promote Employee to CEO',
      description: 'Promote an existing employee to Chief Executive Officer',
      icon: WorkspacePremiumIcon,
      path: '/management/promote-ceo',
      color: '#ffa726',
    },
    {
      title: 'Replace CEO with New Employee',
      description: 'Create a new employee and assign them as CEO',
      icon: SwapHorizIcon,
      path: '/management/replace-ceo',
      color: '#ab47bc',
    },
    {
      title: 'Create New Team',
      description: 'Create a new team and assign team lead, parent team, and department',
      icon: GroupsIcon,
      path: '/management/create-team',
      color: '#81c784',
    },
    {
      title: 'Create New Department',
      description: 'Create a new department to organize teams and employees',
      icon: BusinessIcon,
      path: '/management/create-department',
      color: '#9575cd',
    },
  ];

  return (
    <Box sx={{ px: 3, py: 2 }}>
      <Typography variant="h3" component="h1" gutterBottom sx={{ mb: 4 }}>
        Management
      </Typography>

      <Typography variant="body1" sx={{ mb: 4, color: 'text.secondary' }}>
        Select a management task to perform administrative operations
      </Typography>

      <Box sx={{ maxWidth: 800, mx: 'auto', display: 'flex', flexDirection: 'column', gap: 3 }}>
        {managementTasks.map((task) => {
          const IconComponent = task.icon;
          return (
            <Paper
              key={task.path}
              sx={{
                p: 3,
                cursor: 'pointer',
                transition: 'all 0.2s ease-in-out',
                backgroundColor: 'background.paper',
                minHeight: 120,
                '&:hover': {
                  transform: 'translateY(-4px)',
                  boxShadow: `0 8px 24px ${task.color}33`,
                },
              }}
              onClick={() => navigate(task.path)}
            >
              <Box sx={{ display: 'flex', alignItems: 'flex-start', gap: 2 }}>
                <Box
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    backgroundColor: `${task.color}20`,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    flexShrink: 0,
                  }}
                >
                  <IconComponent sx={{ fontSize: 40, color: task.color }} />
                </Box>
                <Box sx={{ flex: 1 }}>
                  <Typography variant="h5" gutterBottom sx={{ fontWeight: 600 }}>
                    {task.title}
                  </Typography>
                  <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                    {task.description}
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
