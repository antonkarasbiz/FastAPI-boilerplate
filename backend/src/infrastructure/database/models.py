import uuid as uuid_pkg
from datetime import UTC, datetime

from sqlalchemy import DateTime, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, MappedAsDataclass, mapped_column
from sqlalchemy.types import TIMESTAMP


class UUIDMixin(MappedAsDataclass):
    """Mixin to add UUID primary key to database models.

    This mixin provides a standardized UUID primary key for all database models,
    ensuring consistent identification across the application with PostgreSQL's
    built-in UUID generation capabilities.

    Features:
    - UUID4 primary key generation
    - Server-side UUID generation fallback
    - Automatic initialization exclusion
    - PostgreSQL-optimized UUID storage
    - Consistent identification across services

    Attributes:
        uuid: The UUID primary key field with automatic generation.

    Note:
        The UUID is generated using Python's uuid4() function by default,
        with a PostgreSQL server-side fallback using gen_random_uuid().
        This ensures UUID generation even if the client-side generation fails.

        The field is excluded from dataclass initialization (init=False)
        to prevent manual UUID assignment during model creation.

    Example:
        ```python
        from sqlalchemy.orm import DeclarativeBase

        class MyModel(UUIDMixin, DeclarativeBase):
            name: Mapped[str] = mapped_column(String(100))

        # Usage
        model = MyModel(name="example")
        # model.uuid is automatically generated
        ```
    """

    uuid: Mapped[uuid_pkg.UUID] = mapped_column(
        UUID,
        primary_key=True,
        default=uuid_pkg.uuid4,
        server_default=text("gen_random_uuid()"),
        init=False,
    )


class TimestampMixin(MappedAsDataclass):
    """Mixin for adding created_at and updated_at timestamp columns.

    This mixin provides automatic timestamp tracking for database models,
    recording when records are created and last updated with timezone-aware
    datetime values.

    Features:
    - Automatic creation timestamp
    - Automatic update timestamp tracking
    - Timezone-aware datetime storage
    - UTC timezone standardization
    - Dataclass integration with init exclusion

    Attributes:
        created_at: Timestamp when the record was created.
        updated_at: Timestamp when the record was last updated.

    Note:
        Both timestamps use UTC timezone for consistency across different
        deployment environments. The created_at field is never null, while
        updated_at can be null for newly created records.

        The timestamps are excluded from dataclass initialization (init=False)
        to prevent manual timestamp manipulation during model creation.

        For automatic updated_at tracking, you may need to implement
        update triggers or handle updates in your application logic.

    Example:
        ```python
        from sqlalchemy.orm import DeclarativeBase

        class MyModel(TimestampMixin, DeclarativeBase):
            name: Mapped[str] = mapped_column(String(100))

        # Usage
        model = MyModel(name="example")
        # model.created_at and model.updated_at are automatically set
        ```
    """

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(UTC),
        nullable=False,
        init=False,
    )

    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        default_factory=lambda: datetime.now(UTC),
        nullable=True,
        init=False,
    )


class SoftDeleteMixin(MappedAsDataclass):
    """Mixin to add soft delete functionality to database models.

    This mixin provides soft deletion capabilities, allowing records to be
    marked as deleted without actually removing them from the database.
    This is useful for audit trails, data recovery, and maintaining
    referential integrity.

    Features:
    - Soft delete with timestamp tracking
    - Boolean flag for quick deletion checks
    - Audit trail preservation
    - Data recovery capabilities
    - Referential integrity maintenance

    Attributes:
        deleted_at: Timestamp when the record was soft deleted.
        is_deleted: Boolean flag indicating if the record is deleted.

    Note:
        The deleted_at timestamp is nullable and only set when a record
        is soft deleted. The is_deleted boolean provides a quick way to
        check deletion status without null checks.

        Both fields are excluded from dataclass initialization (init=False)
        to prevent manual deletion state manipulation during model creation.

        You'll need to implement query filters to exclude soft-deleted
        records in your application logic unless you specifically want
        to include them.

    Example:
        ```python
        from sqlalchemy.orm import DeclarativeBase

        class MyModel(SoftDeleteMixin, DeclarativeBase):
            name: Mapped[str] = mapped_column(String(100))

        # Usage
        model = MyModel(name="example")

        # Soft delete
        model.deleted_at = datetime.now(UTC)
        model.is_deleted = True

        # Query active records
        active_records = session.query(MyModel).filter(MyModel.is_deleted == False)
        ```
    """

    deleted_at: Mapped[datetime | None] = mapped_column(
        TIMESTAMP(timezone=True),
        nullable=True,
        init=False,
    )
    is_deleted: Mapped[bool] = mapped_column(
        default=False,
        init=False,
    )
