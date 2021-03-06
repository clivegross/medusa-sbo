"""empty message

Revision ID: 065f64b7c8c6
Revises: 6e21436c8d41
Create Date: 2017-08-09 08:45:49.056147

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '065f64b7c8c6'
down_revision = '6e21436c8d41'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('user', sa.Column('authenticated', sa.Boolean(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('user', 'authenticated')
    # ### end Alembic commands ###
