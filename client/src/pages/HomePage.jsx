import { useState, useEffect } from 'react';
import {
  Box,
  TextField,
  Typography,
  List,
  ListItem,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  CircularProgress,
  Alert,
  Paper,
  InputAdornment,
  Divider,
} from '@mui/material';
import SearchIcon from '@mui/icons-material/Search';
import PersonIcon from '@mui/icons-material/Person';
import BusinessIcon from '@mui/icons-material/Business';
import GroupsIcon from '@mui/icons-material/Groups';
import { searchService } from '@/services';

export default function HomePage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Debounced search effect
  useEffect(() => {
    // Clear results if search is empty
    if (!searchQuery.trim()) {
      setResults(null);
      setError(null);
      return;
    }

    // Debounce search to avoid excessive API calls
    const timer = setTimeout(async () => {
      setLoading(true);
      setError(null);

      try {
        const data = await searchService.globalSearch(searchQuery);
        setResults(data);
      } catch (err) {
        setError(err.message);
        setResults(null);
      } finally {
        setLoading(false);
      }
    }, 300); // 300ms debounce

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Calculate total results
  const totalResults =
    (results?.employees?.length || 0) +
    (results?.departments?.length || 0) +
    (results?.teams?.length || 0);

  return (
    <Box sx={{ px: 3, py: 2, maxWidth: 800, mx: 'auto' }}>
      {/* Page Title */}
      <Typography variant="h3" component="h1" gutterBottom sx={{ mb: 3 }}>
        Home
      </Typography>

      {/* Search Bar */}
      <TextField
        fullWidth
        variant="outlined"
        placeholder="Search for people, teams, or departments"
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
        InputProps={{
          startAdornment: (
            <InputAdornment position="start">
              <SearchIcon />
            </InputAdornment>
          ),
        }}
        sx={{ mb: 3 }}
      />

      {/* Loading State */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Results */}
      {!loading && results && (
        <>
          {/* No Results Found */}
          {totalResults === 0 && (
            <Paper sx={{ p: 4, textAlign: 'center', backgroundColor: 'background.paper' }}>
              <Typography variant="body1" color="text.secondary">
                No results found for "{searchQuery}"
              </Typography>
              <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
                Try searching for employee names, departments, or teams
              </Typography>
            </Paper>
          )}

          {/* Employees Section */}
          {results.employees && results.employees.length > 0 && (
            <Paper sx={{ mb: 2, backgroundColor: 'background.paper' }}>
              <Box sx={{ px: 2, py: 1.5, backgroundColor: 'rgba(144, 202, 249, 0.08)' }}>
                <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <PersonIcon fontSize="small" />
                  Employees ({results.employees.length})
                </Typography>
              </Box>
              <Divider />
              <List disablePadding>
                {results.employees.map((employee, index) => (
                  <Box key={employee.id}>
                    <ListItem disablePadding>
                      <ListItemButton>
                        <ListItemIcon>
                          <PersonIcon color="primary" />
                        </ListItemIcon>
                        <ListItemText
                          primary={employee.name}
                          primaryTypographyProps={{ fontWeight: 500 }}
                        />
                      </ListItemButton>
                    </ListItem>
                    {index < results.employees.length - 1 && <Divider />}
                  </Box>
                ))}
              </List>
            </Paper>
          )}

          {/* Departments Section */}
          {results.departments && results.departments.length > 0 && (
            <Paper sx={{ mb: 2, backgroundColor: 'background.paper' }}>
              <Box sx={{ px: 2, py: 1.5, backgroundColor: 'rgba(144, 202, 249, 0.08)' }}>
                <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <BusinessIcon fontSize="small" />
                  Departments ({results.departments.length})
                </Typography>
              </Box>
              <Divider />
              <List disablePadding>
                {results.departments.map((department, index) => (
                  <Box key={department.id}>
                    <ListItem disablePadding>
                      <ListItemButton>
                        <ListItemIcon>
                          <BusinessIcon color="primary" />
                        </ListItemIcon>
                        <ListItemText
                          primary={department.name}
                          primaryTypographyProps={{ fontWeight: 500 }}
                        />
                      </ListItemButton>
                    </ListItem>
                    {index < results.departments.length - 1 && <Divider />}
                  </Box>
                ))}
              </List>
            </Paper>
          )}

          {/* Teams Section */}
          {results.teams && results.teams.length > 0 && (
            <Paper sx={{ mb: 2, backgroundColor: 'background.paper' }}>
              <Box sx={{ px: 2, py: 1.5, backgroundColor: 'rgba(144, 202, 249, 0.08)' }}>
                <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                  <GroupsIcon fontSize="small" />
                  Teams ({results.teams.length})
                </Typography>
              </Box>
              <Divider />
              <List disablePadding>
                {results.teams.map((team, index) => (
                  <Box key={team.id}>
                    <ListItem disablePadding>
                      <ListItemButton>
                        <ListItemIcon>
                          <GroupsIcon color="primary" />
                        </ListItemIcon>
                        <ListItemText
                          primary={team.name}
                          primaryTypographyProps={{ fontWeight: 500 }}
                        />
                      </ListItemButton>
                    </ListItem>
                    {index < results.teams.length - 1 && <Divider />}
                  </Box>
                ))}
              </List>
            </Paper>
          )}
        </>
      )}

      {/* Initial State - No Search Yet */}
      {!loading && !results && !searchQuery && (
        <Paper sx={{ p: 4, textAlign: 'center', backgroundColor: 'background.paper' }}>
          <SearchIcon sx={{ fontSize: 64, color: 'text.secondary', mb: 2 }} />
          <Typography variant="h6" color="text.primary" gutterBottom>
            Search the HRIS System
          </Typography>
          <Typography variant="body2" color="text.secondary">
            Find employees, departments, and teams by name
          </Typography>
        </Paper>
      )}
    </Box>
  );
}
