import { useState, useRef } from 'react';
import { Box, Typography, Paper, CircularProgress, Alert } from '@mui/material';
import { useCEO } from '@/hooks/useCEO';
import OrgChart from '@/components/org-chart/OrgChart';
import DetailModal from '@/components/common/DetailModal';
import EmployeeDetail from '@/components/employees/EmployeeDetail';
import TeamDetail from '@/components/teams/TeamDetail';
import DepartmentDetail from '@/components/departments/DepartmentDetail';

export default function OrgChartPage() {
  const { ceo, loading, error } = useCEO();

  // Modal state for detail views
  const [selectedEmployeeId, setSelectedEmployeeId] = useState(null);
  const [selectedTeamId, setSelectedTeamId] = useState(null);
  const [selectedDepartmentId, setSelectedDepartmentId] = useState(null);

  // Edit mode state for modals
  const [employeeEditMode, setEmployeeEditMode] = useState(false);
  const [employeeSaving, setEmployeeSaving] = useState(false);
  const [teamEditMode, setTeamEditMode] = useState(false);
  const [teamSaving, setTeamSaving] = useState(false);
  const [deptEditMode, setDeptEditMode] = useState(false);
  const [deptSaving, setDeptSaving] = useState(false);

  // Refs to detail components
  const employeeDetailRef = useRef();
  const teamDetailRef = useRef();
  const deptDetailRef = useRef();

  // Handle navigation between modals
  const handleNavigate = (type, id) => {
    if (type === 'employee') {
      setSelectedEmployeeId(id);
    } else if (type === 'team') {
      setSelectedTeamId(id);
    } else if (type === 'department') {
      setSelectedDepartmentId(id);
    }
  };

  // Employee modal edit handlers
  const handleEmployeeEdit = () => {
    employeeDetailRef.current?.enterEditMode();
    setEmployeeEditMode(true);
  };

  const handleEmployeeSave = async () => {
    try {
      setEmployeeSaving(true);
      await employeeDetailRef.current?.save();
      setEmployeeEditMode(false);
    } catch (err) {
      // Error is handled by the detail component
    } finally {
      setEmployeeSaving(false);
    }
  };

  const handleEmployeeCancel = () => {
    employeeDetailRef.current?.cancel();
    setEmployeeEditMode(false);
  };

  // Team modal edit handlers
  const handleTeamEdit = () => {
    teamDetailRef.current?.enterEditMode();
    setTeamEditMode(true);
  };

  const handleTeamSave = async () => {
    try {
      setTeamSaving(true);
      await teamDetailRef.current?.save();
      setTeamEditMode(false);
    } catch (err) {
      // Error is handled by the detail component
    } finally {
      setTeamSaving(false);
    }
  };

  const handleTeamCancel = () => {
    teamDetailRef.current?.cancel();
    setTeamEditMode(false);
  };

  // Department modal edit handlers
  const handleDeptEdit = () => {
    deptDetailRef.current?.enterEditMode();
    setDeptEditMode(true);
  };

  const handleDeptSave = async () => {
    try {
      setDeptSaving(true);
      await deptDetailRef.current?.save();
      setDeptEditMode(false);
    } catch (err) {
      // Error is handled by the detail component
    } finally {
      setDeptSaving(false);
    }
  };

  const handleDeptCancel = () => {
    deptDetailRef.current?.cancel();
    setDeptEditMode(false);
  };

  // Delete handlers
  const handleEmployeeDelete = () => {
    employeeDetailRef.current?.delete();
  };

  const handleEmployeeDeleteSuccess = () => {
    setSelectedEmployeeId(null);
    setEmployeeEditMode(false);
    loadCEO(); // Refresh the org chart
  };

  const handleTeamDelete = () => {
    teamDetailRef.current?.delete();
  };

  const handleTeamDeleteSuccess = () => {
    setSelectedTeamId(null);
    setTeamEditMode(false);
    loadCEO(); // Refresh the org chart
  };

  const handleDeptDelete = () => {
    deptDetailRef.current?.delete();
  };

  const handleDeptDeleteSuccess = () => {
    setSelectedDepartmentId(null);
    setDeptEditMode(false);
    loadCEO(); // Refresh the org chart
  };

  // Handle employee node clicks
  const handleEmployeeClick = (employee) => {
    setSelectedEmployeeId(employee.id);
  };

  return (
    <Box sx={{ px: 3, py: 2 }}>
      {/* Page Title */}
      <Typography variant="h3" component="h1" gutterBottom sx={{ mb: 3 }}>
        Organizational Chart
      </Typography>

      {/* Description */}
      <Typography variant="body1" color="text.secondary" sx={{ mb: 3 }}>
        Explore the company hierarchy. Click on any employee to view details, or expand nodes to see
        their direct reports.
      </Typography>

      {/* Error State */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          Failed to load organizational chart: {error.message || 'Unknown error'}
        </Alert>
      )}

      {/* Loading State */}
      {loading && (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 8 }}>
          <CircularProgress />
        </Box>
      )}

      {/* Org Chart */}
      {!loading && !error && ceo && (
        <Paper sx={{ p: 3, backgroundColor: 'background.paper' }}>
          <OrgChart ceo={ceo} onEmployeeClick={handleEmployeeClick} />
        </Paper>
      )}

      {/* No CEO State */}
      {!loading && !error && !ceo && (
        <Alert severity="info">
          No CEO found. Please create an employee with no manager to establish the organizational
          hierarchy.
        </Alert>
      )}

      {/* Detail Modals */}
      <DetailModal
        open={!!selectedEmployeeId}
        onClose={() => {
          setSelectedEmployeeId(null);
          setEmployeeEditMode(false);
        }}
        title="Employee Details"
        maxWidth="lg"
        showEditButton={true}
        showDeleteButton={true}
        isEditMode={employeeEditMode}
        onEdit={handleEmployeeEdit}
        onDelete={handleEmployeeDelete}
        onSave={handleEmployeeSave}
        onCancel={handleEmployeeCancel}
        isSaving={employeeSaving}
      >
        <EmployeeDetail
          ref={employeeDetailRef}
          employeeId={selectedEmployeeId}
          onNavigate={handleNavigate}
          onDeleteSuccess={handleEmployeeDeleteSuccess}
        />
      </DetailModal>

      <DetailModal
        open={!!selectedTeamId}
        onClose={() => {
          setSelectedTeamId(null);
          setTeamEditMode(false);
        }}
        title="Team Details"
        maxWidth="lg"
        showEditButton={true}
        showDeleteButton={true}
        isEditMode={teamEditMode}
        onEdit={handleTeamEdit}
        onDelete={handleTeamDelete}
        onSave={handleTeamSave}
        onCancel={handleTeamCancel}
        isSaving={teamSaving}
      >
        <TeamDetail
          ref={teamDetailRef}
          teamId={selectedTeamId}
          onNavigate={handleNavigate}
          onDeleteSuccess={handleTeamDeleteSuccess}
        />
      </DetailModal>

      <DetailModal
        open={!!selectedDepartmentId}
        onClose={() => {
          setSelectedDepartmentId(null);
          setDeptEditMode(false);
        }}
        title="Department Details"
        showEditButton={true}
        showDeleteButton={true}
        isEditMode={deptEditMode}
        onEdit={handleDeptEdit}
        onDelete={handleDeptDelete}
        onSave={handleDeptSave}
        onCancel={handleDeptCancel}
        isSaving={deptSaving}
      >
        <DepartmentDetail
          ref={deptDetailRef}
          departmentId={selectedDepartmentId}
          onDeleteSuccess={handleDeptDeleteSuccess}
        />
      </DetailModal>
    </Box>
  );
}
