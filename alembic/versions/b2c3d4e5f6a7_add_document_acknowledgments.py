import sqlalchemy as sa
from alembic import op

revision = "b2c3d4e5f6a7"
down_revision = "a1b2c3d4e5f6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "document_acknowledgments",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "document_id",
            sa.BigInteger(),
            nullable=False,
            comment="ID документа",
        ),
        sa.Column(
            "employee_eid",
            sa.String(),
            nullable=False,
            comment="EID сотрудника, который должен ознакомиться",
        ),
        sa.Column(
            "required_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Дата/время когда требуется ознакомление",
        ),
        sa.Column(
            "acknowledged_at",
            sa.DateTime(),
            nullable=True,
            comment="Дата/время фактического ознакомления",
        ),
        sa.Column(
            "acknowledged_by",
            sa.String(),
            nullable=True,
            comment="EID сотрудника, который ознакомился",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("now()"),
            comment="Дата создания записи",
        ),
        sa.ForeignKeyConstraint(
            ["document_id"],
            ["documents.id"],
            name=op.f("fk_document_acknowledgments_document_id_documents"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_document_acknowledgments")),
        sa.UniqueConstraint(
            "document_id", "employee_eid", name=op.f("uq_document_employee")
        ),
    )

    op.create_index(
        op.f("ix_document_acknowledgments_document_id"),
        "document_acknowledgments",
        ["document_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_acknowledgments_employee_eid"),
        "document_acknowledgments",
        ["employee_eid"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_acknowledgments_acknowledged_at"),
        "document_acknowledgments",
        ["acknowledged_at"],
        unique=False,
    )
    op.create_index(
        op.f("ix_document_acknowledgments_required_at"),
        "document_acknowledgments",
        ["required_at"],
        unique=False,
    )

def downgrade() -> None:
    op.drop_index(
        op.f("ix_document_acknowledgments_required_at"),
        table_name="document_acknowledgments",
    )
    op.drop_index(
        op.f("ix_document_acknowledgments_acknowledged_at"),
        table_name="document_acknowledgments",
    )
    op.drop_index(
        op.f("ix_document_acknowledgments_employee_eid"),
        table_name="document_acknowledgments",
    )
    op.drop_index(
        op.f("ix_document_acknowledgments_document_id"),
        table_name="document_acknowledgments",
    )
    op.drop_table("document_acknowledgments")
