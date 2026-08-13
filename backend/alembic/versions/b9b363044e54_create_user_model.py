"""Update user model

Revision ID: b9b363044e54
Revises: 1a2b3c4d5e6f
Create Date: 2026-07-31 20:53:46.652636

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9b363044e54'
down_revision: Union[str, None] = '1a2b3c4d5e6f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns
    op.add_column('users', sa.Column('full_name', sa.String(length=255), nullable=True))
    op.execute("UPDATE users SET full_name = 'Unknown' WHERE full_name IS NULL")
    op.alter_column('users', 'full_name', existing_type=sa.String(length=255), nullable=False)
    
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), server_default='false', nullable=False))
    op.add_column('users', sa.Column('last_login', sa.DateTime(timezone=True), nullable=True))
    
    # Alter username length
    op.alter_column('users', 'username',
               existing_type=sa.VARCHAR(length=50),
               type_=sa.String(length=255),
               existing_nullable=False)
               
    # Enum type update
    op.execute("ALTER TYPE userrole RENAME TO userrole_old")
    op.execute("CREATE TYPE userrole AS ENUM('ADMIN', 'ML_ENGINEER', 'VIEWER')")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE userrole USING (CASE WHEN role::text = 'USER' THEN 'VIEWER' ELSE role::text END)::userrole")
    op.execute("DROP TYPE userrole_old")


def downgrade() -> None:
    # Revert Enum
    op.execute("ALTER TYPE userrole RENAME TO userrole_new")
    op.execute("CREATE TYPE userrole AS ENUM('ADMIN', 'USER')")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE userrole USING (CASE WHEN role::text = 'VIEWER' THEN 'USER' WHEN role::text = 'ML_ENGINEER' THEN 'USER' ELSE role::text END)::userrole")
    op.execute("DROP TYPE userrole_new")

    op.alter_column('users', 'username',
               existing_type=sa.String(length=255),
               type_=sa.VARCHAR(length=50),
               existing_nullable=False)
    op.drop_column('users', 'last_login')
    op.drop_column('users', 'is_verified')
    op.drop_column('users', 'full_name')