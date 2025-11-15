import { Link, Skeleton, Typography } from '@mui/material';

/**
 * Reusable component for displaying clickable entity links.
 * Handles loading states, null values, and onClick navigation.
 *
 * @param {Object} entity - The entity object with {id, name} properties
 * @param {boolean} loading - Whether the entity is still loading
 * @param {string} type - Entity type: 'employee', 'team', or 'department'
 * @param {function} onNavigate - Callback when link is clicked: (type, id) => void
 * @param {string} secondaryText - Optional secondary text to display (e.g., job title)
 */
export default function EntityLink({
  entity,
  loading,
  type,
  onNavigate,
  secondaryText,
}) {
  // Loading state
  if (loading) {
    return <Skeleton width={120} />;
  }

  // No entity (null or undefined)
  if (!entity) {
    return (
      <Typography variant="body1" color="text.secondary">
        N/A
      </Typography>
    );
  }

  // Entity exists - render clickable link
  const handleClick = (e) => {
    e.preventDefault();
    if (onNavigate && entity.id) {
      onNavigate(type, entity.id);
    }
  };

  return (
    <Link
      component="button"
      variant="body1"
      onClick={handleClick}
      sx={{
        textAlign: 'left',
        cursor: 'pointer',
        '&:hover': {
          textDecoration: 'underline',
        },
      }}
    >
      {entity.name}
      {secondaryText && (
        <Typography
          component="span"
          variant="body2"
          color="text.secondary"
          sx={{ ml: 0.5 }}
        >
          {secondaryText}
        </Typography>
      )}
    </Link>
  );
}
