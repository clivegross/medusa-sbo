#! usr/bin/python3
# -*- coding: utf-8 -*-
#
# Flicket - copyright Paul Bourne: evereux@gmail.com

from app import app

from flask import url_for
from flask_pagedown.fields import PageDownField
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, HiddenField, SubmitField, FileField
from wtforms.fields import SelectMultipleField
from wtforms.validators import DataRequired, Length
from wtforms.widgets import ListWidget, CheckboxInput

from app.ticket.models import (FlicketCategory, FlicketDepartment, FlicketPriority, FlicketTicket, field_size)
from app.models.users import User
from app.ticket.scripts.upload_choice_generator import generate_choices

form_class_button = {'class': 'btn btn-primary'}
form_danger_button = {'class': 'btn btn-danger'}

user_field_size = {
    'username_min': 4,
    'username_max': 24,
    'name_min': 4,
    'name_max': 60,
    'email_min': 6,
    'email_max': 60,
    'password_min': 6,
    'password_max': 60,
    'group_min': 3,
    'group_max': 64,
    'job_title': 64,
    'avatar': 64
}

def does_email_exist(form, field):
    """
    Username must be unique so we check against the database to ensure it doesn't
    :param form:
    :param field:
    :return True / False:
    """
    if form.email.data:
        result = User.query.filter_by(email=form.email.data).count()
        if result == 0:
            field.errors.append('Can\'t find user.')
            return False
    else:
        return False

    return True


def does_department_exist(form, field):
    """
    Username must be unique so we check against the database to ensure it doesn't
    :param form:
    :param field:
    :return True / False:
    """
    result = FlicketDepartment.query.filter_by(department=form.department.data).count()
    if result > 0:
        field.errors.append('Department already exists.')
        return False

    return True


def does_category_exist(form, field):
    """
    Username must be unique so we check against the database to ensure it doesn't
    :param form:
    :param field:
    :return True / False:
    """
    result = FlicketCategory.query.filter_by(category=form.category.data).filter_by(
        department_id=form.department_id.data).count()
    if result > 0:
        field.errors.append('Category already exists.')
        return False

    return True


class CreateTicketForm(FlaskForm):
    def __init__(self, *args, **kwargs):
        form = super(CreateTicketForm, self).__init__(*args, **kwargs)
        self.priority.choices = [(p.id, p.priority) for p in FlicketPriority.query.all()]
        self.category.choices = [(c.id, "{}".format(c.category)) for c in
                                 FlicketCategory.query.order_by(FlicketCategory.category).all()]

    title = StringField('username', validators=[DataRequired(), Length(min=field_size['title_min_length'],
                                                                       max=field_size['title_max_length'])])
    content = PageDownField('content', validators=[DataRequired(), Length(min=field_size['content_min_length'],
                                                                          max=field_size['content_max_length'])])
    priority = SelectField('priority', validators=[DataRequired()], coerce=int)
    category = SelectField('category', validators=[DataRequired()], coerce=int)
    app.config['allowed_extensions'] = app.config['ALLOWED_EXTENSIONS']
    app.config['ticket_upload_folder'] = app.config['TICKET_UPLOAD_FOLDER']
    file = FileField('Upload Documents', render_kw={'multiple': True})
    submit = SubmitField('Submit', render_kw=form_class_button, validators=[DataRequired()])


class MultiCheckBoxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class EditTicketForm(CreateTicketForm):
    def __init__(self, ticket_id, *args, **kwargs):
        self.form = super(EditTicketForm, self).__init__(*args, **kwargs)
        # get ticket data from ticket_id
        ticket = FlicketTicket.query.filter_by(id=ticket_id).first()

        # define the multi select box for document uploads
        uploads = []
        for u in ticket.uploads:
            uploads.append((u.id, u.filename, u.original_filename))
        self.uploads.choices = []
        for x in uploads:
            uri = url_for('view_ticket_uploads', filename=x[1])
            uri_label = '<a href="' + uri + '">' + x[2] + '</a>'
            self.uploads.choices.append((x[0], uri_label))

    uploads = MultiCheckBoxField('Label', coerce=int)
    submit = SubmitField('Edit Ticket', render_kw=form_class_button, validators=[DataRequired()])


class ReplyForm(FlaskForm):
    """ Content form. Displayed when replying too end editing tickets """
    content = PageDownField('Reply', validators=[DataRequired(), Length(min=field_size['content_min_length'],
                                                                        max=field_size['content_max_length'])])
    file = FileField('Upload Documents', render_kw={'multiple': True})
    submit = SubmitField('submit reply', render_kw=form_class_button)
    submit_close = SubmitField('reply and close', render_kw=form_danger_button)


class EditReplyForm(ReplyForm):
    def __init__(self, post_id, *args, **kwargs):
        self.form = super(EditReplyForm, self).__init__(*args, **kwargs)
        self.uploads.choices = generate_choices('Post', id=post_id)

    uploads = MultiCheckBoxField('Label', coerce=int)
    submit = SubmitField('Edit Reply', render_kw=form_class_button, validators=[DataRequired()])


class SearchUserForm(FlaskForm):
    """ Search user. """
    name = StringField('name', validators=[DataRequired(), Length(min=user_field_size['username_min'],
                                                                  max=user_field_size['username_max'])])
    submit = SubmitField('search user', render_kw=form_class_button)


class SearchEmailForm(FlaskForm):
    """ Search email form. """
    email = StringField('email', validators=[DataRequired(), does_email_exist, Length(min=user_field_size['email_min'],
                                                                                      max=user_field_size[
                                                                                          'email_max'])])
    submit = SubmitField('assign', render_kw=form_class_button)


class DepartmentForm(FlaskForm):
    """ Department form. """
    department = StringField('Department', validators=[DataRequired(), Length(min=field_size['department_min_length'],
                                                                              max=field_size['department_max_length']),
                                                       does_department_exist])
    submit = SubmitField('add department', render_kw=form_class_button)


class CategoryForm(FlaskForm):
    """ Category form. """
    category = StringField('Category', validators=[DataRequired(), Length(min=field_size['category_min_length'],
                                                                          max=field_size['category_max_length']),
                                                   does_category_exist])
    department_id = HiddenField('department_id')
    submit = SubmitField('add category', render_kw=form_class_button)
