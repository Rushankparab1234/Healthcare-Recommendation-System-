from alembic import op
from sqlalchemy import Column, DateTime, ForeignKey, String, inspect
from sqlalchemy.sql import func

revision = "0001_saved_providers"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    if "saved_providers" not in inspect(bind).get_table_names():
        op.create_table(
            "saved_providers",
            Column("user_id", String(36), ForeignKey("users.id"), primary_key=True),
            Column("provider_id", String(36), ForeignKey("providers.id"), primary_key=True),
            Column("saved_at", DateTime(), nullable=False, server_default=func.current_timestamp()),
        )


def downgrade() -> None:
    if "saved_providers" in inspect(op.get_bind()).get_table_names():
        op.drop_table("saved_providers")
