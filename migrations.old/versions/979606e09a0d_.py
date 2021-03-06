"""empty message

Revision ID: 979606e09a0d
Revises: 89c55ae20c88
Create Date: 2017-05-31 12:01:41.828785

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '979606e09a0d'
down_revision = '89c55ae20c88'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('alarm', sa.Column('AcknowledgeTime', sa.DateTime(), nullable=True))
    op.add_column('alarm', sa.Column('AcknowledgedBy', sa.String(length=80), nullable=True))
    op.add_column('alarm', sa.Column('AdvancedEvaluationState', sa.Integer(), nullable=True))
    op.add_column('alarm', sa.Column('AlarmState', sa.Integer(), nullable=True))
    op.add_column('alarm', sa.Column('AlarmStateSeqNo', sa.BigInteger(), nullable=True))
    op.add_column('alarm', sa.Column('AlarmText', sa.String(length=1024), nullable=True))
    op.add_column('alarm', sa.Column('AlarmType', sa.String(length=1024), nullable=True))
    op.add_column('alarm', sa.Column('AssignState', sa.Integer(), nullable=True))
    op.add_column('alarm', sa.Column('AssignedTo', sa.String(length=80), nullable=True))
    op.add_column('alarm', sa.Column('AudibleAlert', sa.Boolean(), nullable=True))
    op.add_column('alarm', sa.Column('BasicEvaluationState', sa.Boolean(), nullable=True))
    op.add_column('alarm', sa.Column('Category', sa.String(length=128), nullable=True))
    op.add_column('alarm', sa.Column('CheckedSteps', sa.String(length=512), nullable=True))
    op.add_column('alarm', sa.Column('Command', sa.String(length=128), nullable=True))
    op.add_column('alarm', sa.Column('Count', sa.Integer(), nullable=True))
    op.add_column('alarm', sa.Column('DateTimeStamp', sa.DateTime(), nullable=True))
    op.add_column('alarm', sa.Column('DisabledBy', sa.Integer(), nullable=True))
    op.add_column('alarm', sa.Column('DomainName', sa.String(length=1024), nullable=True))
    op.add_column('alarm', sa.Column('FlashingAlert', sa.Boolean(), nullable=True))
    op.add_column('alarm', sa.Column('HasAttachment', sa.Boolean(), nullable=True))
    op.add_column('alarm', sa.Column('Hidden', sa.Boolean(), nullable=True))
    op.add_column('alarm', sa.Column('Logging', sa.Boolean(), nullable=True))
    op.add_column('alarm', sa.Column('Module', sa.Integer(), nullable=True))
    op.add_column('alarm', sa.Column('MonitoredPoint', sa.String(length=1024), nullable=True))
    op.add_column('alarm', sa.Column('MonitoredValue', sa.String(length=50), nullable=True))
    op.add_column('alarm', sa.Column('OriginatedGUID', sa.String(length=50), nullable=True))
    op.add_column('alarm', sa.Column('PendingCommand', sa.Integer(), nullable=True))
    op.add_column('alarm', sa.Column('PendingState', sa.Integer(), nullable=True))
    op.add_column('alarm', sa.Column('PreviousAlarmState', sa.Integer(), nullable=True))
    op.add_column('alarm', sa.Column('Priority', sa.Integer(), nullable=True))
    op.add_column('alarm', sa.Column('SeqNo', sa.BigInteger(), nullable=True))
    op.add_column('alarm', sa.Column('ServerOffline', sa.Boolean(), nullable=True))
    op.add_column('alarm', sa.Column('Silence', sa.Boolean(), nullable=True))
    op.add_column('alarm', sa.Column('SystemAlarmId', sa.Integer(), nullable=True))
    op.add_column('alarm', sa.Column('SystemEventId', sa.BigInteger(), nullable=True))
    op.add_column('alarm', sa.Column('TriggeredTimestamp', sa.DateTime(), nullable=True))
    op.add_column('alarm', sa.Column('UniqueAlarmId', sa.String(length=50), nullable=True))
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('alarm', 'UniqueAlarmId')
    op.drop_column('alarm', 'TriggeredTimestamp')
    op.drop_column('alarm', 'SystemEventId')
    op.drop_column('alarm', 'SystemAlarmId')
    op.drop_column('alarm', 'Silence')
    op.drop_column('alarm', 'ServerOffline')
    op.drop_column('alarm', 'SeqNo')
    op.drop_column('alarm', 'Priority')
    op.drop_column('alarm', 'PreviousAlarmState')
    op.drop_column('alarm', 'PendingState')
    op.drop_column('alarm', 'PendingCommand')
    op.drop_column('alarm', 'OriginatedGUID')
    op.drop_column('alarm', 'MonitoredValue')
    op.drop_column('alarm', 'MonitoredPoint')
    op.drop_column('alarm', 'Module')
    op.drop_column('alarm', 'Logging')
    op.drop_column('alarm', 'Hidden')
    op.drop_column('alarm', 'HasAttachment')
    op.drop_column('alarm', 'FlashingAlert')
    op.drop_column('alarm', 'DomainName')
    op.drop_column('alarm', 'DisabledBy')
    op.drop_column('alarm', 'DateTimeStamp')
    op.drop_column('alarm', 'Count')
    op.drop_column('alarm', 'Command')
    op.drop_column('alarm', 'CheckedSteps')
    op.drop_column('alarm', 'Category')
    op.drop_column('alarm', 'BasicEvaluationState')
    op.drop_column('alarm', 'AudibleAlert')
    op.drop_column('alarm', 'AssignedTo')
    op.drop_column('alarm', 'AssignState')
    op.drop_column('alarm', 'AlarmType')
    op.drop_column('alarm', 'AlarmText')
    op.drop_column('alarm', 'AlarmStateSeqNo')
    op.drop_column('alarm', 'AlarmState')
    op.drop_column('alarm', 'AdvancedEvaluationState')
    op.drop_column('alarm', 'AcknowledgedBy')
    op.drop_column('alarm', 'AcknowledgeTime')
    # ### end Alembic commands ###
