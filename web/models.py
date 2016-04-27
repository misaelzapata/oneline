# models.py
#from app import db
from mongoengine import *
from flask.ext.admin.contrib.mongoengine import ModelView
import datetime
from wtforms import form, fields, validators
from flask.ext.mongoengine import Document
from flask.ext.mongoengine import MongoEngine
from flask.ext.security import Security, MongoEngineUserDatastore, \
    UserMixin, RoleMixin, login_required, utils, current_user

from mongoengine import StringField, ListField, EmbeddedDocument, \
    EmbeddedDocumentField, IntField, EmailField, DateTimeField, \
    ReferenceField, CASCADE, PolygonField, SortedListField, DictField, \
    BooleanField

# Create user model. For simplicity, it will store passwords in plain text.
# Obviously that's not right thing to do in real world application.
class Role(Document, RoleMixin):
    name = StringField(max_length=80, unique=True)
    description = StringField(max_length=255)

    def __unicode__(self):
        return self.name


class User(Document, UserMixin):
    """Person using the system."""
    username = StringField(required=True)
    password = StringField(required=True)
    first_name = StringField(required=True)
    last_name = StringField(required=True)
    email = EmailField()
    phone = StringField()
    cellphone = StringField()
    active = BooleanField()
    roles = ListField(ReferenceField(Role), default=[])
    meta = {
        'indexes': [{
            'fields': ['email'],
            'unique': True,
            'cache_for': 0  # is needed due to strange bug in PyMongo
        }]
    }

    def __unicode__(self):
        return self.username
    # Flask-Login integration
    def is_authenticated(self):
        return True

    def is_active(self):
        return True

    def is_anonymous(self):
        return False

    def get_id(self):
        return str(self.id)
        

class Contact(Document):
    name = StringField(max_length=200, required=False)
    phone = StringField(max_length=200, required=True)
    date_modified = DateTimeField(default=datetime.datetime.now)


class ContactUser(Document):
    contact_jid = StringField(max_length=200, required=True)
    user_id = StringField(max_length=200, required=True)
    date_modified = DateTimeField(default=datetime.datetime.now)
    

class Message(Document):
    name = StringField(max_length=200, required=True)
    slug = StringField(max_length=200, required=True)
    message = StringField()
    date_modified = DateTimeField(default=datetime.datetime.now)


class SendLog(Document):
    contact = ReferenceField(Contact)
    message = ReferenceField(Message)
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


# Customized admin views


class UserView(ModelView):
    column_filters = ['login', 'email']

    column_searchable_list = ('login', 'email')


class ContactView(ModelView):
    column_filters = ['name', 'phone']

    column_searchable_list = ('name', 'phone')


class MessageView(ModelView):
    column_filters = ['name']
