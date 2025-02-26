"""add text

Revision ID: 460c09e7b51f
Revises: 1537bea90193
Create Date: 2025-02-26 20:14:57.792659

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '460c09e7b51f'
down_revision = '1537bea90193'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('tasks', sa.Column('text', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('tasks', 'text')
    # ### end Alembic commands ###
