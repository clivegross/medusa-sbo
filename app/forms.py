from flask_wtf import FlaskForm
from wtforms import StringField, IntegerField, PasswordField, BooleanField, TextAreaField
from wtforms.validators import DataRequired, Optional

class SiteConfigForm(FlaskForm):
    db_username = StringField('Username', validators=[])
    db_password = PasswordField('Password', validators=[])
    db_address = StringField('Address', validators=[])
    db_port = IntegerField('Port', validators=[Optional()])
    db_name = StringField('Database Name', validators=[])
    inbuildings_enabled = BooleanField('Enabled', validators=[])
    inbuildings_key = StringField('Key', validators=[])

class AddSiteForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    db_username = StringField('Username', validators=[])
    db_password = PasswordField('Password', validators=[])
    db_address = StringField('Address', validators=[])
    db_port = IntegerField('Port', validators=[Optional()])
    db_name = StringField('Database Name', validators=[])

class AddAssetForm(FlaskForm):
    type = StringField('Type', validators=[DataRequired()])
    name = StringField('Name', validators=[DataRequired()])
    location = StringField('Location', validators=[])
    group = StringField('Group', validators=[])
    priority = IntegerField('Priority', validators=[])
    notes = TextAreaField('Notes', validators=[])

class EditAssetForm(FlaskForm):
    name = StringField('Name', validators=[DataRequired()])
    location = StringField('Location', validators=[])
    group = StringField('Group', validators=[])
    priority = IntegerField('Priority', validators=[])
    notes = TextAreaField('Notes', validators=[])