from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6346936bb361'
down_revision = '9c0f2b45e1ae'
branch_labels = None
depends_on = None


def upgrade():
    # Drop tables if they exist
    op.execute('DROP TABLE IF EXISTS Meal')
    op.execute('DROP TABLE IF EXISTS Dietplan')

    # Recreate Dietplan table
    op.create_table(
        'Dietplan',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('name', sa.String(150), nullable=False),
        sa.Column('bmi_category', sa.String(50)),
        sa.Column('diet_preference', sa.String(100)),
        sa.Column('description', sa.Text),
    )

    # Recreate Meal table
    op.create_table(
        'Meal',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('diet_plan_id', sa.Integer, sa.ForeignKey('Dietplan.id'), nullable=False),
        sa.Column('meal_type', sa.String(50), nullable=False),
        sa.Column('item', sa.String(150), nullable=False),
    )


def downgrade():
    # Drop the tables in downgrade
    op.drop_table('Meal')
    op.drop_table('Dietplan')
