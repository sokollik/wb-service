import sqlalchemy as sa
from alembic import op

revision = "a1b2c3d4e5f6"
down_revision = "fc19d934383f"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "roles",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "name",
            sa.String(length=50),
            nullable=False,
            comment="Название роли (EMPLOYEE/CURATOR/ADMIN)",
        ),
        sa.Column(
            "description",
            sa.String(length=255),
            nullable=True,
            comment="Описание роли",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата создания роли",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_roles")),
        sa.UniqueConstraint("name", name=op.f("uq_roles_name")),
    )

    op.create_table(
        "permissions",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "name",
            sa.String(length=100),
            nullable=False,
            comment="Уникальное имя разрешения (news:create, news:edit)",
        ),
        sa.Column(
            "resource",
            sa.String(length=50),
            nullable=False,
            comment="Ресурс (news, comments, profile, documents)",
        ),
        sa.Column(
            "action",
            sa.String(length=20),
            nullable=False,
            comment="Действие (create, read, update, delete, manage)",
        ),
        sa.Column(
            "description",
            sa.String(length=255),
            nullable=True,
            comment="Описание разрешения",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_permissions")),
        sa.UniqueConstraint("name", name=op.f("uq_permissions_name")),
    )

    op.create_table(
        "role_permissions",
        sa.Column(
            "role_id",
            sa.BigInteger(),
            nullable=False,
            comment="ID роли",
        ),
        sa.Column(
            "permission_id",
            sa.BigInteger(),
            nullable=False,
            comment="ID разрешения",
        ),
        sa.ForeignKeyConstraint(
            ["permission_id"],
            ["permissions.id"],
            name=op.f("fk_role_permissions_permission_id_permissions"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name=op.f("fk_role_permissions_role_id_roles"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "role_id", "permission_id", name=op.f("pk_role_permissions")
        ),
    )

    op.create_table(
        "user_roles",
        sa.Column(
            "user_eid",
            sa.String(),
            nullable=False,
            comment="EID пользователя",
        ),
        sa.Column(
            "role_id",
            sa.BigInteger(),
            nullable=False,
            comment="ID роли",
        ),
        sa.Column(
            "granted_by",
            sa.String(),
            nullable=True,
            comment="EID сотрудника, выдавшего роль",
        ),
        sa.Column(
            "granted_at",
            sa.DateTime(),
            server_default=sa.text("now()"),
            nullable=False,
            comment="Дата выдачи роли",
        ),
        sa.ForeignKeyConstraint(
            ["granted_by"],
            ["employee.eid"],
            name=op.f("fk_user_roles_granted_by_employee"),
        ),
        sa.ForeignKeyConstraint(
            ["role_id"],
            ["roles.id"],
            name=op.f("fk_user_roles_role_id_roles"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["user_eid"],
            ["employee.eid"],
            name=op.f("fk_user_roles_user_eid_employee"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("user_eid", "role_id", name=op.f("pk_user_roles")),
    )

    op.create_table(
        "curator_scopes",
        sa.Column("id", sa.BigInteger(), autoincrement=True, nullable=False),
        sa.Column(
            "curator_eid",
            sa.String(),
            nullable=False,
            comment="EID куратора",
        ),
        sa.Column(
            "org_unit_id",
            sa.BigInteger(),
            nullable=False,
            comment="ID подразделения, к которому есть доступ",
        ),
        sa.ForeignKeyConstraint(
            ["curator_eid"],
            ["employee.eid"],
            name=op.f("fk_curator_scopes_curator_eid_employee"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["org_unit_id"],
            ["organization_unit.id"],
            name=op.f("fk_curator_scopes_org_unit_id_organization_unit"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_curator_scopes")),
        sa.UniqueConstraint(
            "curator_eid", "org_unit_id", name=op.f("uq_curator_scope")
        ),
    )

    op.create_index(
        op.f("ix_role_permissions_role_id"),
        "role_permissions",
        ["role_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_role_permissions_permission_id"),
        "role_permissions",
        ["permission_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_user_roles_user_eid"), "user_roles", ["user_eid"], unique=False
    )
    op.create_index(
        op.f("ix_user_roles_role_id"), "user_roles", ["role_id"], unique=False
    )
    op.create_index(
        op.f("ix_curator_scopes_curator_eid"),
        "curator_scopes",
        ["curator_eid"],
        unique=False,
    )
    op.create_index(
        op.f("ix_curator_scopes_org_unit_id"),
        "curator_scopes",
        ["org_unit_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_curator_scopes_org_unit_id"), table_name="curator_scopes")
    op.drop_index(op.f("ix_curator_scopes_curator_eid"), table_name="curator_scopes")
    op.drop_index(op.f("ix_user_roles_role_id"), table_name="user_roles")
    op.drop_index(op.f("ix_user_roles_user_eid"), table_name="user_roles")
    op.drop_index(
        op.f("ix_role_permissions_permission_id"), table_name="role_permissions"
    )
    op.drop_index(
        op.f("ix_role_permissions_role_id"), table_name="role_permissions"
    )
    op.drop_table("curator_scopes")
    op.drop_table("user_roles")
    op.drop_table("role_permissions")
    op.drop_table("permissions")
    op.drop_table("roles")
