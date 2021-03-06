"""empty message

Revision ID: f433fad2b7c4
Revises: be06303bb8e1
Create Date: 2017-12-05 16:30:09.843360

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'f433fad2b7c4'
down_revision = 'be06303bb8e1'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('Deliverable_ITC_map', 'maintenance_revision_number')
    op.drop_column('Deliverable_ITC_map', 'minor_revision_number')
    op.drop_column('Deliverable_ITC_map', 'major_revision_number')
    op.add_column('ITC', sa.Column('maintenance_revision_number', sa.Integer(), nullable=True))
    op.add_column('ITC', sa.Column('major_revision_number', sa.Integer(), nullable=True))
    op.add_column('ITC', sa.Column('minor_revision_number', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('ITC', 'minor_revision_number')
    op.drop_column('ITC', 'major_revision_number')
    op.drop_column('ITC', 'maintenance_revision_number')
    op.add_column('Deliverable_ITC_map', sa.Column('major_revision_number', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.add_column('Deliverable_ITC_map', sa.Column('minor_revision_number', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    op.add_column('Deliverable_ITC_map', sa.Column('maintenance_revision_number', mysql.INTEGER(display_width=11), autoincrement=False, nullable=True))
    # ### end Alembic commands ###
