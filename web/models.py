# models.py
#from app import db
from mongoengine import *
from flask.ext.admin.contrib.mongoengine import ModelView
import flask_admin as flask_admin
import datetime
from wtforms import form, fields, validators
# Create user model. For simplicity, it will store passwords in plain text.
# Obviously that's not right thing to do in real world application.


class User(Document):
    login = StringField(max_length=80, unique=True)
    email = StringField(max_length=120)
    password = StringField(max_length=64)

    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)

    # Required for administrative interface
    def __unicode__(self):
        return self.login


class Contact(Document):
    name = StringField(max_length=200, required=False)
    phone = StringField(max_length=200, required=True)
    date_modified = DateTimeField(default=datetime.datetime.now)


class Message(Document):
    name = StringField(max_length=200, required=True)
    slug = StringField(max_length=200, required=True)
    message = StringField()
    date_modified = DateTimeField(default=datetime.datetime.now)


class SendLog(Document):
    contact = ReferenceField(Contact)
    message = ReferenceField(Message)
    raw_message = StringField()
    sent = BooleanField(default=False)
    date_sent = DateTimeField(default=datetime.datetime.now)


class ReceiveLog(Document):
    user = StringField()
    message = StringField()
    status = StringField(choices=['read', 'unread'])
    date_received = DateTimeField(default=datetime.datetime.now)

# Create customized model view class


class MyModelView(ModelView):

    def is_accessible(self):
        return login.current_user.is_authenticated()


# Create customized index view class
class MyAdminIndexView(flask_admin.AdminIndexView):

    def is_accessible(self):
        return login.current_user.is_authenticated()

# Customized admin views


class UserView(ModelView):
    column_filters = ['login', 'email']

    column_searchable_list = ('login', 'email')


class ContactView(ModelView):
    column_filters = ['name', 'phone']

    column_searchable_list = ('name', 'phone')


class MessageView(ModelView):
    column_filters = ['name']


# Define login and registration forms (for flask-login)
class LoginForm(form.Form):
    login = fields.TextField(validators=[validators.required()])
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        user = self.get_user()

        if user is None:
            raise validators.ValidationError('Invalid user')

        if user.password != self.password.data:
            raise validators.ValidationError('Invalid password')

    def get_user(self):
        return User.objects(login=self.login.data).first()


class RegistrationForm(form.Form):
    login = fields.TextField(validators=[validators.required()])
    email = fields.TextField()
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        if User.objects(login=self.login.data):
            raise validators.ValidationError('Duplicate username')
