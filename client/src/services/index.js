/**
 * Services Index
 * Barrel export for all API services.
 * Allows clean imports: import { employeeService, api } from '@/services'
 */

export { api, ApiError } from './api';
export { employeeService } from './employeeService';
export { departmentService } from './departmentService';
export { teamService } from './teamService';
export { importService } from './importService';
export { exportService, downloadFile } from './exportService';
export { auditLogService } from './auditLogService';
export { searchService } from './searchService';
