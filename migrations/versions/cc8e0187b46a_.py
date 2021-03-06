"""empty message

Revision ID: cc8e0187b46a
Revises: 6299e534470c
Create Date: 2017-08-21 14:49:18.788749

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'cc8e0187b46a'
down_revision = '6299e534470c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('project', sa.Column('assigned_to', sa.String(length=255), nullable=True))
    op.add_column('project', sa.Column('completion_date', sa.DateTime(), nullable=True))
    op.add_column('project', sa.Column('job_number', sa.Integer(), nullable=False))
    op.add_column('project', sa.Column('start_date', sa.DateTime(), nullable=True))
    op.add_column('user', sa.Column('password_active', sa.Boolean(), nullable=True))
    op.add_column('user', sa.Column('password_change_date', sa.DateTime(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'password_change_date')
    op.drop_column('user', 'password_active')
    op.drop_column('project', 'start_date')
    op.drop_column('project', 'job_number')
    op.drop_column('project', 'completion_date')
    op.drop_column('project', 'assigned_to')
    # ### end Alembic commands ###
