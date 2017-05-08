"""empty message

Revision ID: 763e351bf8cb
Revises: 0b651b5fd8e6
Create Date: 2017-05-08 17:17:45.961358

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = '763e351bf8cb'
down_revision = '0b651b5fd8e6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('email_template', sa.Column('Subject', sa.String(length=1024), nullable=True))
    op.drop_column('email_template', 'Title')
    op.alter_column('site', 'CMMS_trigger_priority',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=False)
    op.alter_column('site', 'Email_trigger_priority',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('site', 'Email_trigger_priority',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=True)
    op.alter_column('site', 'CMMS_trigger_priority',
               existing_type=mysql.INTEGER(display_width=11),
               nullable=True)
    op.add_column('email_template', sa.Column('Title', mysql.VARCHAR(length=1024), nullable=True))
    op.drop_column('email_template', 'Subject')
    # ### end Alembic commands ###
