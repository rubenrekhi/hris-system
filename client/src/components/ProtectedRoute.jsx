/**
 * Protected route wrapper component.
 * Ensures user is authenticated before rendering children.
 * Optionally checks for minimum role level using hierarchical role checking.
 */

import { Box, CircularProgress, Container, Paper, Typography } from '@mui/material';
import { useAuth } from '../hooks/useAuth';
import { authService } from '../services/authService';

// Role hierarchy: admin > hr > member
const ROLE_HIERARCHY = {
  member: 1,
  hr: 2,
  admin: 3,
};

function getRoleLevel(role) {
  return ROLE_HIERARCHY[role] || 0;
}

export default function ProtectedRoute({ children, minimumRole = null }) {
  const { user, loading } = useAuth();

  // Show loading spinner while checking authentication
  if (loading) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <CircularProgress />
      </Box>
    );
  }

  // Redirect to login if not authenticated
  if (!user) {
    authService.login();
    return null;
  }

  // Check if user has sufficient role level (hierarchical check)
  if (minimumRole) {
    const userLevel = getRoleLevel(user.role);
    const requiredLevel = getRoleLevel(minimumRole);

    if (userLevel < requiredLevel) {
      return (
        <Container maxWidth="md" sx={{ mt: 8 }}>
          <Paper sx={{ p: 4 }}>
            <Typography variant="h5" gutterBottom>
              Access Denied
            </Typography>
            <Typography variant="body1" color="text.secondary">
              You do not have permission to access this page.
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 2 }}>
              Minimum required role: <strong>{minimumRole}</strong>
            </Typography>
            <Typography variant="body2" color="text.secondary">
              Your current role: <strong>{user.role || 'None'}</strong>
            </Typography>
            <Typography variant="caption" color="text.secondary" sx={{ mt: 2, display: 'block' }}>
              Role hierarchy: admin {'>'} hr {'>'} member
            </Typography>
          </Paper>
        </Container>
      );
    }
  }

  // User is authenticated and has sufficient role level - render children
  return children;
}
