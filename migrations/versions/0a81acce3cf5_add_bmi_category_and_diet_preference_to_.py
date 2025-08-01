"""Add bmi_category and diet_preference to DietPlan

Revision ID: 0a81acce3cf5
Revises: abd01f662949
Create Date: 2025-07-30 20:42:16.389919

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '0a81acce3cf5'
down_revision = 'abd01f662949'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('diet_plan', schema=None) as batch_op:
        batch_op.add_column(sa.Column('bmi_category', sa.String(length=50), nullable=True))
        batch_op.add_column(sa.Column('diet_preference', sa.String(length=100), nullable=True))

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('diet_plan', schema=None) as batch_op:
        batch_op.drop_column('diet_preference')
        batch_op.drop_column('bmi_category')

    # ### end Alembic commands ###
