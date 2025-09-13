/**
 * Main App Component - No Authentication Required
 * Direct access to all application features
 */

import React, { useState } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import {
  ThemeProvider,
  createTheme,
  CssBaseline,
  AppBar,
  Toolbar,
  Typography,
  Button,
  Box,
  Container,
  IconButton,
  Tooltip,
  useMediaQuery,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemButton,
  Divider,
} from '@mui/material';
import {
  Menu as MenuIcon,
  Dashboard as DashboardIcon,
  Analytics as AnalyticsIcon,
  Assessment as AssessmentIcon,
  Settings as SettingsIcon,
  LightMode as LightModeIcon,
  DarkMode as DarkModeIcon,
  Transform as TransformIcon,
} from '@mui/icons-material';

// Import pages
import Dashboard from './pages/Dashboard';
import RepositoryAnalysis from './pages/RepositoryAnalysis';
import AssessmentResultsPage from './pages/AssessmentResults';
import AnalysisProgress from './pages/AnalysisProgress';
import AnalysisResults from './pages/AnalysisResults';

// Create theme
const createAppTheme = (mode: 'light' | 'dark') =>
  createTheme({
    palette: {
      mode,
      primary: {
        main: mode === 'light' ? '#1976d2' : '#90caf9',
      },
      secondary: {
        main: mode === 'light' ? '#dc004e' : '#f48fb1',
      },
      background: {
        default: mode === 'light' ? '#f5f5f5' : '#121212',
        paper: mode === 'light' ? '#ffffff' : '#1e1e1e',
      },
    },
    typography: {
      fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
      h4: {
        fontWeight: 600,
      },
      h5: {
        fontWeight: 600,
      },
      h6: {
        fontWeight: 600,
      },
    },
    components: {
      MuiCard: {
        styleOverrides: {
          root: {
            borderRadius: 12,
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            borderRadius: 8,
            textTransform: 'none',
          },
        },
      },
    },
  });

interface NavigationItem {
  path: string;
  label: string;
  icon: React.ReactNode;
}

const navigationItems: NavigationItem[] = [
  {
    path: '/',
    label: 'Dashboard',
    icon: <DashboardIcon />,
  },
  {
    path: '/analysis',
    label: 'Repository Analysis',
    icon: <AnalyticsIcon />,
  },
  {
    path: '/assessment',
    label: 'Assessment Results',
    icon: <AssessmentIcon />,
  },
  {
    path: '/planning',
    label: 'Transformation Planning',
    icon: <TransformIcon />,
  },
];

const App: React.FC = () => {
  const [darkMode, setDarkMode] = useState(() => {
    const saved = localStorage.getItem('darkMode');
    return saved ? JSON.parse(saved) : false;
  });

  const [mobileOpen, setMobileOpen] = useState(false);

  const isMobile = useMediaQuery('(max-width:600px)');
  const theme = createAppTheme(darkMode ? 'dark' : 'light');

  // Save theme preference
  React.useEffect(() => {
    localStorage.setItem('darkMode', JSON.stringify(darkMode));
  }, [darkMode]);

  const toggleDarkMode = () => {
    setDarkMode(!darkMode);
  };

  const handleDrawerToggle = () => {
    setMobileOpen(!mobileOpen);
  };

  const drawerContent = (
    <Box sx={{ width: 240 }} role="presentation">
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
        <AssessmentIcon color="primary" />
        <Typography variant="h6" color="primary">
          App Analyzer
        </Typography>
      </Box>
      <Divider />
      <List>
        {navigationItems.map((item) => (
          <ListItem key={item.path} disablePadding>
            <ListItemButton
              component="a"
              href={item.path}
              onClick={() => isMobile && setMobileOpen(false)}
            >
              <ListItemIcon>{item.icon}</ListItemIcon>
              <ListItemText primary={item.label} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Box>
  );

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Router>
        <Box sx={{ display: 'flex' }}>
          {/* App Bar */}
          <AppBar
            position="fixed"
            sx={{
              zIndex: theme.zIndex.drawer + 1,
            }}
          >
            <Toolbar>
              {isMobile && (
                <IconButton
                  color="inherit"
                  edge="start"
                  onClick={handleDrawerToggle}
                  sx={{ mr: 2 }}
                >
                  <MenuIcon />
                </IconButton>
              )}

              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1, flex: 1 }}>
                <AssessmentIcon />
                <Typography variant="h6" noWrap>
                  Application Transformation Analyzer
                </Typography>
              </Box>

              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Tooltip title={`Switch to ${darkMode ? 'light' : 'dark'} mode`}>
                  <IconButton color="inherit" onClick={toggleDarkMode}>
                    {darkMode ? <LightModeIcon /> : <DarkModeIcon />}
                  </IconButton>
                </Tooltip>

                <Button
                  color="inherit"
                  startIcon={<SettingsIcon />}
                  sx={{ display: { xs: 'none', sm: 'flex' } }}
                >
                  Settings
                </Button>
              </Box>
            </Toolbar>
          </AppBar>

          {/* Navigation Drawer */}
          {!isMobile && (
            <Drawer
              variant="permanent"
              sx={{
                width: 240,
                flexShrink: 0,
                '& .MuiDrawer-paper': {
                  width: 240,
                  boxSizing: 'border-box',
                },
              }}
            >
              <Toolbar />
              {drawerContent}
            </Drawer>
          )}

          {/* Mobile Drawer */}
          {isMobile && (
            <Drawer
              variant="temporary"
              open={mobileOpen}
              onClose={handleDrawerToggle}
              ModalProps={{
                keepMounted: true,
              }}
              sx={{
                '& .MuiDrawer-paper': {
                  boxSizing: 'border-box',
                  width: 240,
                },
              }}
            >
              {drawerContent}
            </Drawer>
          )}

          {/* Main Content */}
          <Box
            component="main"
            sx={{
              flexGrow: 1,
              p: 3,
              width: { sm: `calc(100% - 240px)` },
            }}
          >
            <Toolbar />
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/analysis" element={<RepositoryAnalysis />} />
              <Route path="/analysis/progress/:jobId" element={<AnalysisProgress />} />
              <Route path="/analysis/results/:jobId" element={<AnalysisResults />} />
              <Route path="/assessment" element={<AssessmentResultsPage />} />
              <Route path="/assessment/:jobId" element={<AssessmentResultsPage />} />
              <Route path="/planning" element={<PlanningPlaceholder />} />
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </Box>
        </Box>
      </Router>
    </ThemeProvider>
  );
};

// Placeholder component for transformation planning
const PlanningPlaceholder: React.FC = () => (
  <Container maxWidth="lg">
    <Typography variant="h4" component="h1" gutterBottom>
      Transformation Planning
    </Typography>
    <Typography variant="body1" color="text.secondary">
      This feature will provide detailed transformation roadmaps and implementation plans based on your 12-factor assessments.
    </Typography>
  </Container>
);

export default App;