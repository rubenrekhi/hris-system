import { useState, useCallback } from 'react';
import { Box, CircularProgress, Typography } from '@mui/material';
import { SimpleTreeView } from '@mui/x-tree-view/SimpleTreeView';
import { TreeItem } from '@mui/x-tree-view/TreeItem';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';
import ChevronRightIcon from '@mui/icons-material/ChevronRight';
import OrgChartNode from './OrgChartNode';
import { employeeService } from '@/services';

/**
 * Organizational chart component with lazy loading of direct reports.
 * Fetches children only when a node is expanded.
 *
 * @param {Object} ceo - The CEO employee (root of the tree)
 * @param {Function} onEmployeeClick - Handler for clicking an employee node
 */
export default function OrgChart({ ceo, onEmployeeClick }) {
  // Track which nodes have been expanded and their children
  const [nodeChildren, setNodeChildren] = useState({});
  // Track which nodes are currently loading
  const [loadingNodes, setLoadingNodes] = useState({});
  // Track which nodes are expanded
  const [expandedNodes, setExpandedNodes] = useState([]);

  /**
   * Fetch direct reports for an employee
   */
  const fetchDirectReports = useCallback(async (employeeId) => {
    // Skip if already loaded or currently loading
    if (nodeChildren[employeeId] || loadingNodes[employeeId]) {
      return;
    }

    setLoadingNodes((prev) => ({ ...prev, [employeeId]: true }));

    try {
      const directReports = await employeeService.getDirectReports(employeeId);
      setNodeChildren((prev) => ({
        ...prev,
        [employeeId]: directReports || [],
      }));
    } catch (error) {
      console.error('Failed to fetch direct reports:', error);
      setNodeChildren((prev) => ({
        ...prev,
        [employeeId]: [],
      }));
    } finally {
      setLoadingNodes((prev) => {
        const newLoading = { ...prev };
        delete newLoading[employeeId];
        return newLoading;
      });
    }
  }, [nodeChildren, loadingNodes]);

  /**
   * Handle node expansion
   */
  const handleNodeToggle = useCallback(
    (event, nodeIds) => {
      setExpandedNodes(nodeIds);

      // Find newly expanded nodes
      const newlyExpanded = nodeIds.filter((id) => !expandedNodes.includes(id));

      // Fetch children for newly expanded nodes
      newlyExpanded.forEach((nodeId) => {
        fetchDirectReports(nodeId);
      });
    },
    [expandedNodes, fetchDirectReports]
  );

  /**
   * Recursively render tree nodes
   */
  const renderTreeNode = (employee) => {
    const nodeId = employee.id;
    const children = nodeChildren[nodeId];
    const isLoading = loadingNodes[nodeId];
    const isExpanded = expandedNodes.includes(nodeId);
    const hasLoadedChildren = children !== undefined;

    return (
      <TreeItem
        key={nodeId}
        itemId={nodeId}
        label={
          <Box sx={{ py: 1 }}>
            <OrgChartNode
              employee={employee}
              onClick={(e) => {
                e.stopPropagation();
                onEmployeeClick?.(employee);
              }}
            />
          </Box>
        }
        sx={{
          '& > .MuiTreeItem-content': {
            paddingLeft: 2,
          },
          '& > .MuiCollapse-root': {
            marginLeft: '100px',
          },
          '& .MuiTreeItem-group': {
            marginLeft: '100px',
            paddingLeft: '40px',
            borderLeft: '2px solid',
            borderColor: 'divider',
          },
        }}
      >
        {/* Show placeholder if not yet loaded (to display expand icon) */}
        {!hasLoadedChildren && !isLoading && (
          <TreeItem
            itemId={`${nodeId}-placeholder`}
            label={
              <Box sx={{ py: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                  Click to expand
                </Typography>
              </Box>
            }
          />
        )}

        {/* Show loading indicator while fetching */}
        {isLoading && (
          <TreeItem
            itemId={`${nodeId}-loading`}
            label={
              <Box sx={{ py: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
                <CircularProgress size={16} />
                <Typography variant="body2" color="text.secondary">
                  Loading direct reports...
                </Typography>
              </Box>
            }
          />
        )}

        {/* Render children recursively */}
        {!isLoading && hasLoadedChildren && children.length > 0 && children.map((child) => renderTreeNode(child))}

        {/* Show "No direct reports" message if expanded with no children */}
        {!isLoading && hasLoadedChildren && children.length === 0 && (
          <TreeItem
            itemId={`${nodeId}-empty`}
            label={
              <Box sx={{ py: 1 }}>
                <Typography variant="body2" color="text.secondary" sx={{ fontStyle: 'italic' }}>
                  No direct reports
                </Typography>
              </Box>
            }
          />
        )}
      </TreeItem>
    );
  };

  if (!ceo) {
    return null;
  }

  return (
    <Box sx={{ width: '100%', overflowX: 'auto' }}>
      <SimpleTreeView
        expandedItems={expandedNodes}
        onExpandedItemsChange={handleNodeToggle}
        slots={{
          expandIcon: ChevronRightIcon,
          collapseIcon: ExpandMoreIcon,
        }}
        sx={{
          flexGrow: 1,
          overflowY: 'auto',
          '& .MuiTreeItem-content': {
            py: 0.5,
          },
          '& .MuiTreeItem-group': {
            marginLeft: 100,
            paddingLeft: 8,
            borderLeft: '2px solid',
            borderColor: 'divider',
          },
        }}
      >
        {renderTreeNode(ceo)}
      </SimpleTreeView>
    </Box>
  );
}
