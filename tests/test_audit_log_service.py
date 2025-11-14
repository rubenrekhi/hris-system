"""
test_audit_log_service.py
--------------------------
Test suite for AuditLogService business logic.

Testing Strategy:
1. Use in-memory SQLite for fast, isolated tests
2. Each test gets a fresh database session via fixtures
3. Test both happy paths and edge cases
4. Verify service doesn't auto-commit (router responsibility)
5. Test all filtering and pagination combinations
"""

import pytest
from datetime import datetime, timedelta
from uuid import uuid4
from sqlalchemy.orm import Session

from services.AuditLogService import AuditLogService
from models.AuditLogModel import AuditLog, EntityType, ChangeType


class TestCreateAuditLog:
    """Tests for AuditLogService.create_audit_log()"""

    def test_create_audit_log_with_all_fields(self, db_session: Session):
        """Should create audit log with all fields populated."""
        # Arrange
        service = AuditLogService(db_session)
        entity_id = uuid4()
        user_id = uuid4()
        previous_state = {"name": "John Doe", "status": "active"}
        new_state = {"name": "Jane Doe", "status": "active"}

        # Act
        audit_log = service.create_audit_log(
            entity_type=EntityType.EMPLOYEE,
            entity_id=entity_id,
            change_type=ChangeType.UPDATE,
            previous_state=previous_state,
            new_state=new_state,
            changed_by_user_id=user_id,
        )
        db_session.flush()  # Flush to generate ID

        # Assert
        assert audit_log is not None
        assert audit_log.id is not None  # Auto-generated
        assert audit_log.entity_type == EntityType.EMPLOYEE
        assert audit_log.entity_id == entity_id
        assert audit_log.change_type == ChangeType.UPDATE
        assert audit_log.previous_state == previous_state
        assert audit_log.new_state == new_state
        assert audit_log.changed_by_user_id == user_id

    def test_create_audit_log_with_minimal_fields(self, db_session: Session):
        """Should create audit log with only required fields."""
        # Arrange
        service = AuditLogService(db_session)
        entity_id = uuid4()

        # Act
        audit_log = service.create_audit_log(
            entity_type=EntityType.DEPARTMENT,
            entity_id=entity_id,
            change_type=ChangeType.CREATE,
        )
        db_session.flush()  # Flush to generate ID

        # Assert
        assert audit_log is not None
        assert audit_log.id is not None
        assert audit_log.entity_type == EntityType.DEPARTMENT
        assert audit_log.entity_id == entity_id
        assert audit_log.change_type == ChangeType.CREATE
        assert audit_log.previous_state is None
        assert audit_log.new_state is None
        assert audit_log.changed_by_user_id is None

    def test_create_audit_log_does_not_commit(self, db_session: Session):
        """Should add to session but NOT commit (router's responsibility)."""
        # Arrange
        service = AuditLogService(db_session)
        entity_id = uuid4()

        # Act
        service.create_audit_log(
            entity_type=EntityType.USER,
            entity_id=entity_id,
            change_type=ChangeType.DELETE,
        )

        # Assert - rollback and verify nothing persisted
        db_session.rollback()
        result = db_session.query(AuditLog).all()
        assert len(result) == 0  # Should be empty after rollback


class TestBulkCreateAuditLogs:
    """Tests for AuditLogService.bulk_create_audit_logs()"""

    def test_bulk_create_audit_logs_success(self, db_session: Session):
        """Should create multiple audit logs with identical fields."""
        # Arrange
        service = AuditLogService(db_session)
        entity_ids = [uuid4(), uuid4(), uuid4()]
        user_id = uuid4()
        previous_state = {"manager_id": str(uuid4())}
        new_state = {"manager_id": str(uuid4())}

        # Act
        audit_logs = service.bulk_create_audit_logs(
            entity_type=EntityType.EMPLOYEE,
            entity_ids=entity_ids,
            change_type=ChangeType.UPDATE,
            previous_state=previous_state,
            new_state=new_state,
            changed_by_user_id=user_id,
        )
        db_session.flush()  # Flush to generate IDs

        # Assert
        assert len(audit_logs) == 3
        for i, audit_log in enumerate(audit_logs):
            assert audit_log.id is not None
            assert audit_log.entity_type == EntityType.EMPLOYEE
            assert audit_log.entity_id == entity_ids[i]
            assert audit_log.change_type == ChangeType.UPDATE
            assert audit_log.previous_state == previous_state
            assert audit_log.new_state == new_state
            assert audit_log.changed_by_user_id == user_id

    def test_bulk_create_audit_logs_minimal_fields(self, db_session: Session):
        """Should create bulk audit logs with only required fields."""
        # Arrange
        service = AuditLogService(db_session)
        entity_ids = [uuid4(), uuid4()]

        # Act
        audit_logs = service.bulk_create_audit_logs(
            entity_type=EntityType.DEPARTMENT,
            entity_ids=entity_ids,
            change_type=ChangeType.CREATE,
        )
        db_session.flush()

        # Assert
        assert len(audit_logs) == 2
        for i, audit_log in enumerate(audit_logs):
            assert audit_log.id is not None
            assert audit_log.entity_type == EntityType.DEPARTMENT
            assert audit_log.entity_id == entity_ids[i]
            assert audit_log.change_type == ChangeType.CREATE
            assert audit_log.previous_state is None
            assert audit_log.new_state is None
            assert audit_log.changed_by_user_id is None

    def test_bulk_create_audit_logs_empty_list(self, db_session: Session):
        """Should return empty list when entity_ids is empty."""
        # Arrange
        service = AuditLogService(db_session)
        entity_ids = []

        # Act
        audit_logs = service.bulk_create_audit_logs(
            entity_type=EntityType.EMPLOYEE,
            entity_ids=entity_ids,
            change_type=ChangeType.UPDATE,
        )

        # Assert
        assert audit_logs == []
        assert len(audit_logs) == 0

    def test_bulk_create_audit_logs_single_entity(self, db_session: Session):
        """Should work correctly with a single entity ID."""
        # Arrange
        service = AuditLogService(db_session)
        entity_ids = [uuid4()]
        user_id = uuid4()

        # Act
        audit_logs = service.bulk_create_audit_logs(
            entity_type=EntityType.TEAM,
            entity_ids=entity_ids,
            change_type=ChangeType.DELETE,
            previous_state={"name": "Team A"},
            changed_by_user_id=user_id,
        )
        db_session.flush()

        # Assert
        assert len(audit_logs) == 1
        assert audit_logs[0].entity_id == entity_ids[0]
        assert audit_logs[0].entity_type == EntityType.TEAM
        assert audit_logs[0].change_type == ChangeType.DELETE
        assert audit_logs[0].previous_state == {"name": "Team A"}
        assert audit_logs[0].changed_by_user_id == user_id

    def test_bulk_create_audit_logs_large_batch(self, db_session: Session):
        """Should efficiently create large batch of audit logs."""
        # Arrange
        service = AuditLogService(db_session)
        entity_ids = [uuid4() for _ in range(100)]
        user_id = uuid4()

        # Act
        audit_logs = service.bulk_create_audit_logs(
            entity_type=EntityType.EMPLOYEE,
            entity_ids=entity_ids,
            change_type=ChangeType.UPDATE,
            previous_state={"status": "ACTIVE"},
            new_state={"status": "ON_LEAVE"},
            changed_by_user_id=user_id,
        )
        db_session.flush()

        # Assert
        assert len(audit_logs) == 100
        # Verify all were added to session (pending commit)
        pending_logs = db_session.query(AuditLog).filter(
            AuditLog.changed_by_user_id == user_id
        ).all()
        assert len(pending_logs) == 100

    def test_bulk_create_audit_logs_does_not_commit(self, db_session: Session):
        """Should add to session but NOT commit (router's responsibility)."""
        # Arrange
        service = AuditLogService(db_session)
        entity_ids = [uuid4(), uuid4()]

        # Act
        service.bulk_create_audit_logs(
            entity_type=EntityType.USER,
            entity_ids=entity_ids,
            change_type=ChangeType.UPDATE,
        )

        # Assert - rollback and verify nothing persisted
        db_session.rollback()
        result = db_session.query(AuditLog).all()
        assert len(result) == 0  # Should be empty after rollback

    def test_bulk_create_audit_logs_unique_ids(self, db_session: Session):
        """Should create logs with unique IDs even when created in bulk."""
        # Arrange
        service = AuditLogService(db_session)
        entity_ids = [uuid4() for _ in range(10)]

        # Act
        audit_logs = service.bulk_create_audit_logs(
            entity_type=EntityType.EMPLOYEE,
            entity_ids=entity_ids,
            change_type=ChangeType.CREATE,
        )
        db_session.flush()

        # Assert
        log_ids = [log.id for log in audit_logs]
        assert len(log_ids) == len(set(log_ids))  # All IDs are unique

    def test_bulk_create_audit_logs_returns_all_objects(self, db_session: Session):
        """Should return all created AuditLog objects in same order."""
        # Arrange
        service = AuditLogService(db_session)
        entity_ids = [uuid4(), uuid4(), uuid4(), uuid4(), uuid4()]

        # Act
        audit_logs = service.bulk_create_audit_logs(
            entity_type=EntityType.DEPARTMENT,
            entity_ids=entity_ids,
            change_type=ChangeType.UPDATE,
        )
        db_session.flush()

        # Assert
        assert len(audit_logs) == len(entity_ids)
        for i, audit_log in enumerate(audit_logs):
            assert audit_log.entity_id == entity_ids[i]


class TestGetAuditLog:
    """Tests for AuditLogService.get_audit_log()"""

    def test_get_existing_audit_log(self, db_session: Session):
        """Should retrieve existing audit log by ID."""
        # Arrange
        service = AuditLogService(db_session)
        entity_id = uuid4()
        audit_log = service.create_audit_log(
            entity_type=EntityType.TEAM,
            entity_id=entity_id,
            change_type=ChangeType.CREATE,
            new_state={"name": "Engineering"},
        )
        db_session.commit()
        log_id = audit_log.id

        # Act
        retrieved = service.get_audit_log(log_id)

        # Assert
        assert retrieved is not None
        assert retrieved.id == log_id
        assert retrieved.entity_type == EntityType.TEAM
        assert retrieved.entity_id == entity_id
        assert retrieved.new_state == {"name": "Engineering"}

    def test_get_nonexistent_audit_log(self, db_session: Session):
        """Should return None for non-existent audit log ID."""
        # Arrange
        service = AuditLogService(db_session)
        fake_id = uuid4()

        # Act
        result = service.get_audit_log(fake_id)

        # Assert
        assert result is None


class TestListAuditLogs:
    """Tests for AuditLogService.list_audit_logs()"""

    @pytest.fixture
    def sample_logs(self, db_session: Session):
        """Create sample audit logs for testing list operations."""
        service = AuditLogService(db_session)
        user_id_1 = uuid4()
        user_id_2 = uuid4()
        entity_id_1 = uuid4()
        entity_id_2 = uuid4()

        logs = [
            # Employee logs
            service.create_audit_log(
                entity_type=EntityType.EMPLOYEE,
                entity_id=entity_id_1,
                change_type=ChangeType.CREATE,
                changed_by_user_id=user_id_1,
            ),
            service.create_audit_log(
                entity_type=EntityType.EMPLOYEE,
                entity_id=entity_id_1,
                change_type=ChangeType.UPDATE,
                changed_by_user_id=user_id_1,
            ),
            # Department logs
            service.create_audit_log(
                entity_type=EntityType.DEPARTMENT,
                entity_id=entity_id_2,
                change_type=ChangeType.CREATE,
                changed_by_user_id=user_id_2,
            ),
            service.create_audit_log(
                entity_type=EntityType.DEPARTMENT,
                entity_id=entity_id_2,
                change_type=ChangeType.DELETE,
                changed_by_user_id=user_id_2,
            ),
            # Team log
            service.create_audit_log(
                entity_type=EntityType.TEAM,
                entity_id=uuid4(),
                change_type=ChangeType.CREATE,
                changed_by_user_id=user_id_1,
            ),
        ]
        db_session.commit()

        return {
            "logs": logs,
            "user_id_1": user_id_1,
            "user_id_2": user_id_2,
            "entity_id_1": entity_id_1,
            "entity_id_2": entity_id_2,
        }

    def test_list_all_logs_no_filters(self, db_session: Session, sample_logs):
        """Should list all audit logs without filters."""
        # Arrange
        service = AuditLogService(db_session)

        # Act
        items, total = service.list_audit_logs()

        # Assert
        assert total == 5
        assert len(items) == 5

    def test_list_logs_filter_by_entity_type(self, db_session: Session, sample_logs):
        """Should filter audit logs by entity_type."""
        # Arrange
        service = AuditLogService(db_session)

        # Act
        items, total = service.list_audit_logs(entity_type=EntityType.EMPLOYEE)

        # Assert
        assert total == 2
        assert len(items) == 2
        assert all(log.entity_type == EntityType.EMPLOYEE for log in items)

    def test_list_logs_filter_by_entity_id(self, db_session: Session, sample_logs):
        """Should filter audit logs by entity_id."""
        # Arrange
        service = AuditLogService(db_session)
        entity_id = sample_logs["entity_id_1"]

        # Act
        items, total = service.list_audit_logs(entity_id=entity_id)

        # Assert
        assert total == 2
        assert len(items) == 2
        assert all(log.entity_id == entity_id for log in items)

    def test_list_logs_filter_by_change_type(self, db_session: Session, sample_logs):
        """Should filter audit logs by change_type."""
        # Arrange
        service = AuditLogService(db_session)

        # Act
        items, total = service.list_audit_logs(change_type=ChangeType.CREATE)

        # Assert
        assert total == 3
        assert len(items) == 3
        assert all(log.change_type == ChangeType.CREATE for log in items)

    def test_list_logs_filter_by_changed_by_user_id(self, db_session: Session, sample_logs):
        """Should filter audit logs by changed_by_user_id."""
        # Arrange
        service = AuditLogService(db_session)
        user_id = sample_logs["user_id_1"]

        # Act
        items, total = service.list_audit_logs(changed_by_user_id=user_id)

        # Assert
        assert total == 3
        assert len(items) == 3
        assert all(log.changed_by_user_id == user_id for log in items)

    def test_list_logs_filter_by_date_range(self, db_session: Session, sample_logs):
        """Should filter audit logs by date range."""
        # Arrange
        service = AuditLogService(db_session)

        # Act - filter with a very wide date range that includes all test data
        # Since SQLite doesn't have server-side func.now(), we use a wide range
        date_from = datetime.now() - timedelta(days=1)
        date_to = datetime.now() + timedelta(days=1)
        items, total = service.list_audit_logs(date_from=date_from, date_to=date_to)

        # Assert - should find the sample logs created by the fixture
        # Since created_at is set client-side in SQLite, they should be included
        assert total == 5  # All sample logs
        assert len(items) == 5

    def test_list_logs_pagination_limit(self, db_session: Session, sample_logs):
        """Should paginate results with limit."""
        # Arrange
        service = AuditLogService(db_session)

        # Act
        items, total = service.list_audit_logs(limit=2)

        # Assert
        assert total == 5  # Total count unchanged
        assert len(items) == 2  # Only 2 items returned

    def test_list_logs_pagination_offset(self, db_session: Session, sample_logs):
        """Should paginate results with offset."""
        # Arrange
        service = AuditLogService(db_session)

        # Act - get first page
        first_page, _ = service.list_audit_logs(limit=2, offset=0)
        # Act - get second page
        second_page, total = service.list_audit_logs(limit=2, offset=2)

        # Assert
        assert total == 5
        assert len(second_page) == 2
        assert first_page[0].id != second_page[0].id  # Different items

    def test_list_logs_order_desc(self, db_session: Session, sample_logs):
        """Should order logs by created_at descending (newest first)."""
        # Arrange
        service = AuditLogService(db_session)

        # Act
        items, _ = service.list_audit_logs(order="desc")

        # Assert
        assert len(items) == 5
        # Verify descending order
        for i in range(len(items) - 1):
            assert items[i].created_at >= items[i + 1].created_at

    def test_list_logs_order_asc(self, db_session: Session, sample_logs):
        """Should order logs by created_at ascending (oldest first)."""
        # Arrange
        service = AuditLogService(db_session)

        # Act
        items, _ = service.list_audit_logs(order="asc")

        # Assert
        assert len(items) == 5
        # Verify ascending order
        for i in range(len(items) - 1):
            assert items[i].created_at <= items[i + 1].created_at

    def test_list_logs_multiple_filters(self, db_session: Session, sample_logs):
        """Should apply multiple filters simultaneously."""
        # Arrange
        service = AuditLogService(db_session)
        entity_id = sample_logs["entity_id_1"]
        user_id = sample_logs["user_id_1"]

        # Act
        items, total = service.list_audit_logs(
            entity_type=EntityType.EMPLOYEE,
            entity_id=entity_id,
            change_type=ChangeType.UPDATE,
            changed_by_user_id=user_id,
        )

        # Assert
        assert total == 1
        assert len(items) == 1
        assert items[0].entity_type == EntityType.EMPLOYEE
        assert items[0].entity_id == entity_id
        assert items[0].change_type == ChangeType.UPDATE
        assert items[0].changed_by_user_id == user_id

    def test_list_logs_empty_result(self, db_session: Session, sample_logs):
        """Should return empty list when no logs match filters."""
        # Arrange
        service = AuditLogService(db_session)
        fake_id = uuid4()

        # Act
        items, total = service.list_audit_logs(entity_id=fake_id)

        # Assert
        assert total == 0
        assert len(items) == 0
