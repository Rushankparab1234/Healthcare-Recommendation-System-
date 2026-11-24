import sqlalchemy as sa
from alembic import op

revision = "0002_consent_and_integrity"
down_revision = "0001_saved_providers"
branch_labels = None
depends_on = None


def upgrade() -> None:
    with op.batch_alter_table("patient_profiles") as batch_op:
        batch_op.add_column(sa.Column("consent_research_at", sa.DateTime(timezone=True), nullable=True))

    with op.batch_alter_table("recommendations") as batch_op:
        batch_op.create_foreign_key(
            "fk_recommendations_assessment_id",
            "symptom_assessments",
            ["assessment_id"],
            ["id"],
        )
        batch_op.create_index("ix_recommendations_assessment_id", ["assessment_id"])


def downgrade() -> None:
    with op.batch_alter_table("recommendations") as batch_op:
        batch_op.drop_index("ix_recommendations_assessment_id")
        batch_op.drop_constraint("fk_recommendations_assessment_id", type_="foreignkey")

    with op.batch_alter_table("patient_profiles") as batch_op:
        batch_op.drop_column("consent_research_at")
