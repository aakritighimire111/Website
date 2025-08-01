"""Initial migration

Revision ID: 0f48ebda646c
Revises: 95c5ebb9a676
Create Date: 2025-07-30 19:52:29.953503

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0f48ebda646c'
down_revision = '95c5ebb9a676'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('workout', schema=None) as batch_op:
        batch_op.add_column(sa.Column('preferred_workout_type', sa.String(length=50), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('workout', schema=None) as batch_op:
        batch_op.drop_column('preferred_workout_type')

    # ### end Alembic commands ###
