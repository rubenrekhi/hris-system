/**
 * Login page component.
 * Provides a simple interface to redirect users to WorkOS authentication.
 */

import { Box, Button, Container, Paper, Typography } from '@mui/material';
import LoginIcon from '@mui/icons-material/Login';
import { authService } from '../services/authService';

export default function Login() {
  const handleLogin = () => {
    authService.login();
  };

  return (
    <Container maxWidth="sm">
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <Paper
          elevation={3}
          sx={{
            p: 6,
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            width: '100%',
          }}
        >
          <Typography variant="h4" component="h1" gutterBottom>
            HRIS System
          </Typography>
          <Typography variant="body1" color="text.secondary" sx={{ mb: 4, textAlign: 'center' }}>
            Please sign in to access the Human Resources Information System
          </Typography>
          <Button
            variant="contained"
            size="large"
            startIcon={<LoginIcon />}
            onClick={handleLogin}
            fullWidth
            sx={{ py: 1.5 }}
          >
            Sign In with WorkOS
          </Button>
        </Paper>
      </Box>
    </Container>
  );
}
