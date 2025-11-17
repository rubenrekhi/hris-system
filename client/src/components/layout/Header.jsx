import { useState } from 'react';
import {
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  IconButton,
  Drawer,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  useTheme,
  useMediaQuery,
  Chip,
  Snackbar,
  Alert
} from '@mui/material';
import { Link, useLocation } from 'react-router-dom';
import MenuIcon from '@mui/icons-material/Menu';
import HomeIcon from '@mui/icons-material/Home';
import GroupIcon from '@mui/icons-material/Group';
import AccountTreeIcon from '@mui/icons-material/AccountTree';
import AssignmentIcon from '@mui/icons-material/Assignment';
import BusinessIcon from '@mui/icons-material/Business';
import BarChartIcon from '@mui/icons-material/BarChart';
import AdminPanelSettingsIcon from '@mui/icons-material/AdminPanelSettings';
import LogoutIcon from '@mui/icons-material/Logout';
import { cache } from '@/utils/cache';
import { departmentService, teamService, employeeService, auditLogService } from '@/services';
import { useAuth } from '@/hooks/useAuth';
import DetailModal from '@/components/common/DetailModal';
import EmployeeDetail from '@/components/employees/EmployeeDetail';

/**
 * Header component with top navigation bar.
 * Displays app title and navigation links with icons.
 * Responsive: Shows hamburger menu on mobile, full nav on desktop.
 */
export default function Header() {
  const location = useLocation();
  const theme = useTheme();
  const isMobile = useMediaQuery(theme.breakpoints.down('md'));
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const { user, logout } = useAuth();

  // Employee profile modal state
  const [selectedEmployeeId, setSelectedEmployeeId] = useState(null);
  const [showWarning, setShowWarning] = useState(false);

  /**
   * Handle clicking on user name to view their employee profile
   */
  const handleNameClick = () => {
    if (user?.employee_id) {
      setSelectedEmployeeId(user.employee_id);
    } else {
      setShowWarning(true);
    }
  };

  const navItems = [
    { label: 'Home', path: '/', icon: <HomeIcon /> },
    { label: 'Employee Directory', path: '/employees', icon: <GroupIcon /> },
    { label: 'Org Chart', path: '/org-chart', icon: <AccountTreeIcon /> },
    { label: 'Audits', path: '/audits', icon: <AssignmentIcon /> },
    { label: 'Departments', path: '/teams', icon: <BusinessIcon /> },
    { label: 'Reports', path: '/reports', icon: <BarChartIcon /> },
    { label: 'Management', path: '/management', icon: <AdminPanelSettingsIcon /> },
  ];

  const handleDrawerToggle = () => {
    setMobileMenuOpen(!mobileMenuOpen);
  };

  const handleDrawerClose = () => {
    setMobileMenuOpen(false);
  };

  /**
   * Prefetch data for a route on hover to reduce loading time.
   * Only prefetches if data is not already cached.
   */
  const handlePrefetch = async (path) => {
    try {
      // Prefetch for Employee Directory page
      if (path === '/employees') {
        // Prefetch departments and teams for filter dropdowns
        if (!cache.has('departments')) {
          const deptData = await departmentService.listDepartments({ limit: 100 });
          cache.set('departments', deptData);
        }
        if (!cache.has('teams')) {
          const teamData = await teamService.listTeams({ limit: 100 });
          cache.set('teams', teamData);
        }
        // Prefetch first page of employees (no filters)
        if (!cache.has('employees_page_0')) {
          const employeesData = await employeeService.listEmployees({ limit: 25, offset: 0 });
          cache.set('employees_page_0', employeesData);
        }
      }

      // Prefetch for Departments page
      if (path === '/teams') {
        // Prefetch departments for department cards
        if (!cache.has('departments')) {
          const deptData = await departmentService.listDepartments({ limit: 100 });
          cache.set('departments', deptData);
        }
      }

      // Prefetch for Audits page
      if (path === '/audits') {
        // Prefetch first page of audit logs (no filters, newest first)
        if (!cache.has('audit_logs_page_0')) {
          const auditLogsData = await auditLogService.listAuditLogs({
            limit: 25,
            offset: 0,
            order: 'desc',
          });
          cache.set('audit_logs_page_0', auditLogsData);
        }
      }
    } catch (err) {
      // Silently fail - prefetch is optional, don't break navigation
      console.debug('Prefetch failed for', path, err);
    }
  };

  return (
    <>
      <AppBar position="fixed" elevation={0}>
        <Toolbar>
          {/* Hamburger Menu Button - Mobile Only */}
          <IconButton
            color="inherit"
            aria-label="open navigation menu"
            edge="start"
            onClick={handleDrawerToggle}
            sx={{ mr: 2, display: { xs: 'block', md: 'none' } }}
          >
            <MenuIcon />
          </IconButton>

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

          {/* Navigation Buttons - Desktop Only */}
          <Box sx={{ flexGrow: 1, display: { xs: 'none', md: 'flex' }, gap: 0.5 }}>
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;

              return (
                <Button
                  key={item.path}
                  component={Link}
                  to={item.path}
                  startIcon={item.icon}
                  onMouseEnter={() => handlePrefetch(item.path)}
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

          {/* User Info and Logout - Desktop and Mobile */}
          {user && (
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
              {/* User Name - Desktop Only */}
              <Typography
                variant="body2"
                onClick={handleNameClick}
                sx={{
                  display: { xs: 'none', md: 'block' },
                  color: 'text.secondary',
                  cursor: 'pointer',
                  '&:hover': {
                    color: 'primary.main',
                    textDecoration: 'underline',
                  },
                }}
              >
                {user.name}
              </Typography>

              {/* Role Badge */}
              <Chip
                label={user.role || 'member'}
                size="small"
                color={user.role === 'admin' ? 'error' : user.role === 'hr' ? 'warning' : 'default'}
                sx={{ textTransform: 'uppercase', fontWeight: 600 }}
              />

              {/* Logout Button */}
              <Button
                variant="outlined"
                size="small"
                startIcon={<LogoutIcon />}
                onClick={logout}
                sx={{
                  borderColor: 'rgba(255, 255, 255, 0.23)',
                  color: 'text.secondary',
                  '&:hover': {
                    borderColor: 'error.main',
                    color: 'error.main',
                    backgroundColor: 'rgba(211, 47, 47, 0.04)',
                  },
                }}
              >
                Logout
              </Button>
            </Box>
          )}
        </Toolbar>
      </AppBar>

      {/* Mobile Navigation Drawer */}
      <Drawer
        anchor="left"
        open={mobileMenuOpen}
        onClose={handleDrawerClose}
        sx={{
          display: { xs: 'block', md: 'none' },
          '& .MuiDrawer-paper': {
            width: 280,
          },
        }}
      >
        <Box sx={{ pt: 2 }}>
          <Typography
            variant="h6"
            sx={{
              px: 2,
              pb: 2,
              fontWeight: 600,
              letterSpacing: '0.5px',
            }}
          >
            HRIS System
          </Typography>
          <List>
            {navItems.map((item) => {
              const isActive = location.pathname === item.path;

              return (
                <ListItem key={item.path} disablePadding>
                  <ListItemButton
                    component={Link}
                    to={item.path}
                    onClick={handleDrawerClose}
                    onMouseEnter={() => handlePrefetch(item.path)}
                    selected={isActive}
                    sx={{
                      '&.Mui-selected': {
                        backgroundColor: 'primary.dark',
                        '&:hover': {
                          backgroundColor: 'primary.dark',
                        },
                      },
                    }}
                  >
                    <ListItemIcon sx={{ color: isActive ? 'primary.main' : 'text.secondary' }}>
                      {item.icon}
                    </ListItemIcon>
                    <ListItemText
                      primary={item.label}
                      sx={{
                        '& .MuiListItemText-primary': {
                          fontWeight: isActive ? 600 : 400,
                          color: isActive ? 'primary.main' : 'text.primary',
                        },
                      }}
                    />
                  </ListItemButton>
                </ListItem>
              );
            })}
          </List>
        </Box>
      </Drawer>

      {/* Employee Profile Modal */}
      {selectedEmployeeId && (
        <DetailModal
          open={!!selectedEmployeeId}
          onClose={() => setSelectedEmployeeId(null)}
          title="My Employee Profile"
          maxWidth="md"
        >
          <EmployeeDetail employeeId={selectedEmployeeId} />
        </DetailModal>
      )}

      {/* Warning Snackbar for users without employee record */}
      <Snackbar
        open={showWarning}
        autoHideDuration={6000}
        onClose={() => setShowWarning(false)}
        anchorOrigin={{ vertical: 'top', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setShowWarning(false)}
          severity="warning"
          sx={{ width: '100%' }}
        >
          No employee record is associated with your account.
        </Alert>
      </Snackbar>
    </>
  );
}
