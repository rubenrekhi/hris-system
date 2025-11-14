import { Box } from '@mui/material';
import Header from './Header';

/**
 * Main layout wrapper component.
 * Includes header and main content area with proper spacing.
 */
export default function Layout({ children }) {
  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <Header />

      {/* Main content area with top padding to account for fixed AppBar */}
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          pt: 10, // Add padding-top for fixed AppBar (64px default + extra space)
          px: 3,
          pb: 3,
          backgroundColor: 'background.default',
        }}
      >
        {children}
      </Box>
    </Box>
  );
}
