"""init

Revision ID: 3033138c586e
Revises: 
Create Date: 2025-02-10 17:59:35.286435

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3033138c586e'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('tasks',
    sa.Column('product', sa.String(), nullable=True),
    sa.Column('weight', sa.Integer(), nullable=True),
    sa.Column('kilocalories_per100g', sa.Integer(), nullable=True),
    sa.Column('proteins_per100g', sa.Integer(), nullable=True),
    sa.Column('fats_per100g', sa.Integer(), nullable=True),
    sa.Column('carbohydrates_per100g', sa.Integer(), nullable=True),
    sa.Column('fiber_per100g', sa.Integer(), nullable=True),
    sa.Column('error', sa.String(), nullable=True),
    sa.Column('id', sa.Uuid(), server_default=sa.text('gen_random_uuid()'), nullable=False),
    sa.Column('created_at', sa.DateTime(), server_default=sa.text("(now() at time zone 'utc')"), nullable=False),
    sa.Column('updated_at', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_tasks_id'), 'tasks', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_tasks_id'), table_name='tasks')
    op.drop_table('tasks')
    # ### end Alembic commands ###
