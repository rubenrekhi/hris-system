import { useState, useRef } from 'react';
import {
  Box,
  Typography,
  Paper,
  Button,
  IconButton,
  Alert,
  CircularProgress,
  Collapse,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  Divider,
} from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import DownloadIcon from '@mui/icons-material/Download';
import InfoIcon from '@mui/icons-material/Info';
import CheckCircleIcon from '@mui/icons-material/CheckCircle';
import ErrorIcon from '@mui/icons-material/Error';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ExpandLessIcon from '@mui/icons-material/ExpandLess';
import DescriptionIcon from '@mui/icons-material/Description';
import { importService } from '@/services';
import { generateSampleCSV, generateErrorReportCSV, downloadCSV } from '@/utils/csvHelpers';

export default function BulkImportPage() {
  const navigate = useNavigate();
  const fileInputRef = useRef(null);

  // File state
  const [selectedFile, setSelectedFile] = useState(null);
  const [fileError, setFileError] = useState(null);

  // Upload state
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState(null);

  // Results state
  const [results, setResults] = useState(null);
  const [failedRowsOpen, setFailedRowsOpen] = useState(false);

  // UI state
  const [instructionsOpen, setInstructionsOpen] = useState(true);

  // Handle file selection
  const handleFileChange = (e) => {
    const file = e.target.files[0];
    setFileError(null);
    setError(null);
    setResults(null);

    if (!file) {
      setSelectedFile(null);
      return;
    }

    // Validate file type
    const validTypes = ['text/csv', 'application/vnd.ms-excel'];
    const validExtensions = ['.csv', '.xlsx'];
    const hasValidType =
      validTypes.includes(file.type) || validExtensions.some((ext) => file.name.endsWith(ext));

    if (!hasValidType) {
      setFileError('Invalid file type. Please upload a CSV or Excel (.xlsx) file.');
      setSelectedFile(null);
      return;
    }

    // Validate file size (10MB limit)
    const maxSize = 10 * 1024 * 1024; // 10MB
    if (file.size > maxSize) {
      setFileError('File too large. Maximum size is 10MB.');
      setSelectedFile(null);
      return;
    }

    setSelectedFile(file);
  };

  // Handle file upload button click
  const handleUploadClick = () => {
    fileInputRef.current?.click();
  };

  // Handle import
  const handleImport = async () => {
    if (!selectedFile) return;

    setUploading(true);
    setError(null);
    setResults(null);

    try {
      const result = await importService.importEmployees(selectedFile);
      setResults(result);

      // Auto-expand failed rows if there are any
      if (result.failed_rows && result.failed_rows.length > 0) {
        setFailedRowsOpen(true);
      }
    } catch (err) {
      console.error('Import failed:', err);
      setError(err.message || 'Failed to import file. Please check the format and try again.');
    } finally {
      setUploading(false);
    }
  };

  // Handle download sample template
  const handleDownloadTemplate = () => {
    const blob = generateSampleCSV();
    downloadCSV(blob, 'employee-import-template.csv');
  };

  // Handle download error report
  const handleDownloadErrorReport = () => {
    if (!results?.failed_rows) return;
    const blob = generateErrorReportCSV(results.failed_rows);
    downloadCSV(blob, `import-errors-${new Date().toISOString().split('T')[0]}.csv`);
  };

  // Handle import another file
  const handleReset = () => {
    setSelectedFile(null);
    setResults(null);
    setError(null);
    setFileError(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  };

  // Format file size for display
  const formatFileSize = (bytes) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
  };

  return (
    <Box sx={{ px: 3, py: 2 }}>
      {/* Back Button and Title */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2, mb: 3 }}>
        <IconButton onClick={() => navigate('/management')} sx={{ color: 'primary.main' }}>
          <ArrowBackIcon />
        </IconButton>
        <Typography variant="h3" component="h1">
          Bulk Import Employees
        </Typography>
      </Box>

      <Typography variant="body1" sx={{ mb: 4, color: 'text.secondary' }}>
        Upload a CSV or Excel file to import multiple employees at once
      </Typography>

      {/* General Error Alert */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }} onClose={() => setError(null)}>
          {error}
        </Alert>
      )}

      {/* Success Results */}
      {results && (
        <Alert
          severity={results.failed_rows?.length > 0 ? 'warning' : 'success'}
          icon={results.failed_rows?.length > 0 ? <ErrorIcon /> : <CheckCircleIcon />}
          sx={{ mb: 3 }}
        >
          <Typography variant="body1" sx={{ fontWeight: 600 }}>
            {results.failed_rows?.length > 0
              ? `Partially completed: ${results.successful_imports} of ${results.total_rows} employees imported`
              : `Success! ${results.successful_imports} of ${results.total_rows} employees imported`}
          </Typography>
          {results.warnings && results.warnings.length > 0 && (
            <Typography variant="body2" sx={{ mt: 1 }}>
              {results.warnings.length} warning(s) - check imported data
            </Typography>
          )}
        </Alert>
      )}

      {/* Instructions Panel */}
      <Paper sx={{ mb: 3, backgroundColor: 'background.paper' }}>
        <Box
          sx={{
            px: 2,
            py: 1.5,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'space-between',
            cursor: 'pointer',
            backgroundColor: 'rgba(144, 202, 249, 0.08)',
          }}
          onClick={() => setInstructionsOpen(!instructionsOpen)}
        >
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <InfoIcon />
            <Typography variant="h6">Import Instructions</Typography>
          </Box>
          <IconButton size="small">
            {instructionsOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
          </IconButton>
        </Box>

        <Collapse in={instructionsOpen}>
          <Box sx={{ p: 3 }}>
            {/* Download Template Button */}
            <Button
              variant="outlined"
              startIcon={<DownloadIcon />}
              onClick={handleDownloadTemplate}
              sx={{ mb: 3 }}
            >
              Download Sample Template
            </Button>

            <Typography variant="h6" gutterBottom>
              File Format Requirements
            </Typography>

            <Box sx={{ mb: 3 }}>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Supported formats:</strong> CSV (.csv) or Excel (.xlsx)
              </Typography>
              <Typography variant="body2" sx={{ mb: 1 }}>
                <strong>Maximum file size:</strong> 10MB
              </Typography>
            </Box>

            <Typography variant="h6" gutterBottom>
              Required Columns
            </Typography>
            <Box component="ul" sx={{ mt: 1, mb: 2, pl: 3 }}>
              <li>
                <Typography variant="body2">
                  <strong>name</strong> - Full name of the employee
                </Typography>
              </li>
              <li>
                <Typography variant="body2">
                  <strong>email</strong> - Unique email address
                </Typography>
              </li>
            </Box>

            <Typography variant="h6" gutterBottom>
              Optional Columns
            </Typography>
            <Box component="ul" sx={{ mt: 1, pl: 3 }}>
              <li>
                <Typography variant="body2">
                  <strong>title</strong> - Job title
                </Typography>
              </li>
              <li>
                <Typography variant="body2">
                  <strong>hired_on</strong> - Hire date (YYYY-MM-DD format)
                </Typography>
              </li>
              <li>
                <Typography variant="body2">
                  <strong>salary</strong> - Annual salary (number only)
                </Typography>
              </li>
              <li>
                <Typography variant="body2">
                  <strong>status</strong> - ACTIVE or ON_LEAVE (defaults to ACTIVE)
                </Typography>
              </li>
              <li>
                <Typography variant="body2">
                  <strong>manager_email</strong> - Email of direct manager
                </Typography>
              </li>
              <li>
                <Typography variant="body2">
                  <strong>department_name</strong> - Department name
                </Typography>
              </li>
              <li>
                <Typography variant="body2">
                  <strong>team_name</strong> - Team name
                </Typography>
              </li>
            </Box>
          </Box>
        </Collapse>
      </Paper>

      {/* File Upload Section */}
      {!results && (
        <Paper sx={{ p: 3, backgroundColor: 'background.paper', mb: 3 }}>
          <Typography variant="h6" gutterBottom>
            Select File
          </Typography>

          <input
            ref={fileInputRef}
            type="file"
            accept=".csv,.xlsx,application/vnd.ms-excel,text/csv"
            style={{ display: 'none' }}
            onChange={handleFileChange}
          />

          {!selectedFile ? (
            <Box
              sx={{
                border: '2px dashed',
                borderColor: fileError ? 'error.main' : 'primary.main',
                borderRadius: 2,
                p: 4,
                textAlign: 'center',
                backgroundColor: fileError ? 'rgba(211, 47, 47, 0.05)' : 'rgba(144, 202, 249, 0.05)',
                cursor: 'pointer',
                transition: 'all 0.2s',
                '&:hover': {
                  backgroundColor: fileError ? 'rgba(211, 47, 47, 0.1)' : 'rgba(144, 202, 249, 0.1)',
                },
              }}
              onClick={handleUploadClick}
            >
              <CloudUploadIcon sx={{ fontSize: 48, color: fileError ? 'error.main' : 'primary.main', mb: 2 }} />
              <Typography variant="h6" gutterBottom>
                Click to select file
              </Typography>
              <Typography variant="body2" color="text.secondary">
                CSV or Excel (.xlsx) files only
              </Typography>
              {fileError && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  {fileError}
                </Alert>
              )}
            </Box>
          ) : (
            <Box>
              <Paper
                sx={{
                  p: 2,
                  backgroundColor: 'rgba(144, 202, 249, 0.1)',
                  border: '1px solid',
                  borderColor: 'primary.main',
                }}
              >
                <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
                  <DescriptionIcon sx={{ fontSize: 40, color: 'primary.main' }} />
                  <Box sx={{ flex: 1 }}>
                    <Typography variant="body1" sx={{ fontWeight: 600 }}>
                      {selectedFile.name}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      {formatFileSize(selectedFile.size)}
                    </Typography>
                  </Box>
                  <Button variant="outlined" size="small" onClick={handleUploadClick}>
                    Change File
                  </Button>
                </Box>
              </Paper>

              <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
                <Button variant="outlined" onClick={handleReset}>
                  Cancel
                </Button>
                <Button
                  variant="contained"
                  size="large"
                  startIcon={uploading ? <CircularProgress size={20} /> : <CloudUploadIcon />}
                  onClick={handleImport}
                  disabled={uploading}
                >
                  {uploading ? 'Importing...' : 'Import Employees'}
                </Button>
              </Box>
            </Box>
          )}
        </Paper>
      )}

      {/* Results Section - Failed Rows */}
      {results && results.failed_rows && results.failed_rows.length > 0 && (
        <Paper sx={{ mb: 3, backgroundColor: 'background.paper' }}>
          <Box
            sx={{
              px: 2,
              py: 1.5,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              cursor: 'pointer',
              backgroundColor: 'rgba(211, 47, 47, 0.08)',
            }}
            onClick={() => setFailedRowsOpen(!failedRowsOpen)}
          >
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <ErrorIcon sx={{ color: 'error.main' }} />
              <Typography variant="h6">Failed Imports ({results.failed_rows.length} rows)</Typography>
            </Box>
            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Button
                variant="outlined"
                size="small"
                startIcon={<DownloadIcon />}
                onClick={(e) => {
                  e.stopPropagation();
                  handleDownloadErrorReport();
                }}
              >
                Download Error Report
              </Button>
              <IconButton size="small">
                {failedRowsOpen ? <ExpandLessIcon /> : <ExpandMoreIcon />}
              </IconButton>
            </Box>
          </Box>

          <Collapse in={failedRowsOpen}>
            <Box sx={{ p: 2 }}>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Row #</TableCell>
                      <TableCell>Name</TableCell>
                      <TableCell>Email</TableCell>
                      <TableCell>Error Message</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {results.failed_rows.map((failedRow, index) => (
                      <TableRow key={index}>
                        <TableCell>{failedRow.row_number}</TableCell>
                        <TableCell>{failedRow.row_data?.name || '-'}</TableCell>
                        <TableCell>{failedRow.email || failedRow.row_data?.email || '-'}</TableCell>
                        <TableCell>
                          <Typography variant="body2" color="error">
                            {failedRow.error_message}
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Box>
          </Collapse>
        </Paper>
      )}

      {/* Results Section - Actions */}
      {results && (
        <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center' }}>
          <Button variant="outlined" size="large" onClick={() => navigate('/employees')}>
            View Employee Directory
          </Button>
          <Button variant="contained" size="large" onClick={handleReset} startIcon={<CloudUploadIcon />}>
            Import Another File
          </Button>
        </Box>
      )}
    </Box>
  );
}
