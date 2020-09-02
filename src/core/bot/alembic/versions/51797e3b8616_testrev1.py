"""testrev1

Revision ID: 51797e3b8616
Revises:
Create Date: 2020-09-02 12:22:52.909468

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '51797e3b8616'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'account',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(50), nullable=False),
        sa.Column('description', sa.Unicode(200)),
    )


def downgrade():
    op.drop_table('account')
