import { createTheme } from '@mui/material/styles';

/**
 * Dark theme configuration for the HRIS application.
 * Inspired by Material UI dashboard templates.
 */
export const darkTheme = createTheme({
  palette: {
    mode: 'dark',
    primary: {
      main: '#90caf9', // Light blue for dark mode
      light: '#b3d9f2',
      dark: '#648dae',
      contrastText: '#000',
    },
    secondary: {
      main: '#f48fb1', // Light pink accent
      light: '#f6a5c0',
      dark: '#aa647b',
      contrastText: '#000',
    },
    background: {
      default: '#0a1929', // Deep blue-black (MUI dashboard style)
      paper: '#1a2027', // Slightly lighter for cards/surfaces
    },
    text: {
      primary: '#fff',
      secondary: 'rgba(255, 255, 255, 0.7)',
    },
    divider: 'rgba(255, 255, 255, 0.12)',
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
    h1: {
      fontSize: '2.5rem',
      fontWeight: 500,
    },
    h2: {
      fontSize: '2rem',
      fontWeight: 500,
    },
    h3: {
      fontSize: '1.75rem',
      fontWeight: 500,
    },
    h4: {
      fontSize: '1.5rem',
      fontWeight: 500,
    },
    h5: {
      fontSize: '1.25rem',
      fontWeight: 500,
    },
    h6: {
      fontSize: '1rem',
      fontWeight: 500,
    },
  },
  components: {
    MuiAppBar: {
      styleOverrides: {
        root: {
          backgroundColor: '#1a2027',
          backgroundImage: 'none',
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none', // Keep button text normal case
          borderRadius: 8,
        },
      },
    },
    MuiCard: {
      styleOverrides: {
        root: {
          backgroundImage: 'none',
        },
      },
    },
  },
});
