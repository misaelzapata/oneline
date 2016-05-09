from flask.ext.admin.contrib.mongoengine import ModelView
import datetime
from flask.ext.mongoengine import Document
from flask.ext.security import Security, MongoEngineUserDatastore, \
    UserMixin, RoleMixin, login_required, utils, current_user
from mongoengine import StringField, ListField, EmbeddedDocument, \
    EmbeddedDocumentField, IntField, EmailField, DateTimeField, \
    ReferenceField, CASCADE, PolygonField, SortedListField, DictField, \
    BooleanField

# Create user model. For simplicity, it will store passwords in plain text.
# Obviously that's not right thing to do in real world application.


class Role(Document, RoleMixin):
    """Role of the user, for now just operator and admin"""
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
    # Flask-Login integration with mongo

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


class OutgoingMessages(Document):
    contact = StringField()
    operator_id = StringField()
    message = StringField()
    sent = BooleanField(default='false')
    date_sent = DateTimeField()
    created = DateTimeField(default=datetime.datetime.now)


class IncomingMessages(Document):
    message = StringField()
    contact = StringField()
    status = StringField(choices=['read', 'unread'])
    modified = DateTimeField()
    created = DateTimeField(default=datetime.datetime.now)
    date_readed = DateTimeField()
    user = ReferenceField(User, required=False)

# Following classes are also used on the admin, are defined here because otherwise we end up with a circular import


class MyModelView(ModelView):
    """
    Basic Mixing, use it on every view of the admin to ensure that the view can only be accessed by admins.
    """
    def is_accessible(self):
        if login.current_user.is_authenticated:
            if login.current_user.has_role("admin"):
                return True
        return False


# Customized admin views


class UserView(MyModelView):
    column_filters = ['login', 'email']
    column_searchable_list = ('login', 'email')


class ContactView(MyModelView):
    column_filters = ['name', 'phone']
    column_searchable_list = ('name', 'phone')


class MessageView(MyModelView):
    column_filters = ['name']
