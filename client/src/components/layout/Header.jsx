import { AppBar, Toolbar, Typography, Button, Box } from '@mui/material';
import { Link, useLocation } from 'react-router-dom';
import HomeIcon from '@mui/icons-material/Home';
import GroupIcon from '@mui/icons-material/Group';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import AssignmentIcon from '@mui/icons-material/Assignment';
import BusinessIcon from '@mui/icons-material/Business';
import BarChartIcon from '@mui/icons-material/BarChart';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';

/**
 * Header component with top navigation bar.
 * Displays app title and navigation links with icons.
 */
export default function Header() {
  const location = useLocation();

  const navItems = [
    { label: 'Home', path: '/', icon: <HomeIcon /> },
    { label: 'Employee Directory', path: '/employees', icon: <GroupIcon /> },
    { label: 'Org Chart', path: '/org-chart', icon: <AccountTreeIcon /> },
    { label: 'Audits', path: '/audits', icon: <AssignmentIcon /> },
    { label: 'Teams', path: '/teams', icon: <BusinessIcon /> },
    { label: 'Reports', path: '/reports', icon: <BarChartIcon /> },
    { label: 'Management', path: '/management', icon: <AdminPanelSettingsIcon /> },
  ];

  return (
    <AppBar position="fixed" elevation={0}>
      <Toolbar>
        {/* App Title */}
        <Typography
          variant="h6"
          component="div"
          sx={{
            flexGrow: 0,
            fontWeight: 600,
            mr: 4,
            letterSpacing: '0.5px',
          }}
        >
          HRIS System
        </Typography>

        {/* Navigation Buttons */}
        <Box sx={{ flexGrow: 1, display: 'flex', gap: 0.5 }}>
          {navItems.map((item) => {
            const isActive = location.pathname === item.path;

            return (
              <Button
                key={item.path}
                component={Link}
                to={item.path}
                startIcon={item.icon}
                sx={{
                  color: isActive ? 'primary.main' : 'text.secondary',
                  fontWeight: isActive ? 600 : 400,
                  px: 2,
                  '&:hover': {
                    backgroundColor: 'rgba(255, 255, 255, 0.08)',
                    color: 'primary.light',
                  },
                }}
              >
                {item.label}
              </Button>
            );
          })}
        </Box>
      </Toolbar>
    </AppBar>
  );
}
