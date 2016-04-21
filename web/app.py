# app.py
import json
import datetime
import redis
from string import Template
from flask import Flask
from flask import request, render_template, url_for, redirect
from config import BaseConfig, DevConfig
from flask.ext.mongoengine import MongoEngine
from flask.ext.admin import Admin
from flask.ext.admin.contrib.mongoengine import ModelView
from flask.ext.mongoengine import MongoEngine
from flask.ext.security import Security, MongoEngineUserDatastore, \
    UserMixin, RoleMixin, login_required, utils, current_user

from flask.ext import admin, login
from flask.ext.admin import helpers

import flask_admin as flask_admin

from flask_debugtoolbar import DebugToolbarExtension
from flask_security import utils

from models import Contact, Message, User, SendLog, ReceiveLog, \
    MyModelView, MyAdminIndexView, UserView, \
    ContactView, MessageView, \
    LoginForm, RegistrationForm

from wtforms.fields import PasswordField


app = Flask(__name__)
app.config.from_object(DevConfig)
app.config['SECRET_KEY'] = '123456790'

app.config['DEBUG_TB_PANELS'] = [
    'flask.ext.mongoengine.panels.MongoDebugPanel']
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
toolbar = DebugToolbarExtension(app)

# Create models
db = MongoEngine(app)

_redis = redis.StrictRedis(host='redis', port=6379)

# ADMIN #


class Role(db.Document, RoleMixin):
    name = db.StringField(max_length=80, unique=True)
    description = db.StringField(max_length=255)

    def __unicode__(self):
        return self.name

    # __hash__ is required to avoid the exception TypeError: unhashable type: 'Role' when saving a User
    def __hash__(self):
        return hash(self.name)


class User(db.Document, UserMixin):
    email = db.StringField(max_length=255)
    password = db.StringField(max_length=255)
    active = db.BooleanField(default=True)
    confirmed_at = db.DateTimeField()
    roles = db.ListField(db.ReferenceField(Role), default=[])

# Setup Flask-Security
user_datastore = MongoEngineUserDatastore(db, User, Role)
security = Security(app, user_datastore)


# Create a user to test with
@app.before_first_request
def create_user():
    # Create the Roles "admin" and "end-user" -- unless they already exist
    user_datastore.find_or_create_role(name='admin', description='Administrator')

    # Create two Users for testing purposes -- unless they already exists.
    # In each case, use Flask-Security utility function to encrypt the password.
    encrypted_password = utils.encrypt_password('que sabroso el caramel en el delta123')
    if not user_datastore.get_user('dropkek@oneline.net'):
        user_datastore.create_user(email='dropkek@oneline.net', password=encrypted_password)

# Views
@app.route('/admin')
@login_required
def home():
    return render_template('admin.html')


# Customized User model for SQL-Admin
class UserAdmin(ModelView):

    # Don't display the password on the list of Users
    column_exclude_list = ('password',)

    # Don't include the standard password field when creating or editing a User (but see below)
    form_excluded_columns = ('password',)

    # Automatically display human-readable names for the current and available Roles when creating or editing a User
    column_auto_select_related = True

    # Prevent administration of Users unless the currently logged-in user has the "admin" role
    def is_accessible(self):
        return current_user.has_role('admin')

    # On the form for creating or editing a User, don't display a field corresponding to the model's password field.
    # There are two reasons for this. First, we want to encrypt the password before storing in the database. Second,
    # we want to use a password field (with the input masked) rather than a regular text field.
    def scaffold_form(self):

        # Start with the standard form as provided by Flask-Admin. We've already told Flask-Admin to exclude the
        # password field from this form.
        form_class = super(UserAdmin, self).scaffold_form()

        # Add a password field, naming it "password2" and labeling it "New Password".
        form_class.password2 = PasswordField('New Password')
        return form_class

    # This callback executes when the user saves changes to a newly-created or edited User -- before the changes are
    # committed to the database.
    def on_model_change(self, form, model, is_created):

        # If the password field isn't blank...
        if len(model.password2):

            # ... then encrypt the new password prior to storing it in the database. If the password field is blank,
            # the existing password in the database will be retained.
            model.password = utils.encrypt_password(model.password2)


# Customized Role model for SQL-Admin
class RoleAdmin(ModelView):

    # Prevent administration of Roles unless the currently logged-in user has the "admin" role
    def is_accessible(self):
        return current_user.has_role('admin')

# Initialize Flask-Admin
admin = Admin(app)

# Add Flask-Admin views for Users and Roles
admin.add_view(UserAdmin(User))
admin.add_view(RoleAdmin(Role))
# ADMIN #


# Initialize flask-login
def init_login():
    login_manager = login.LoginManager()
    login_manager.setup_app(app)

    # Create user loader function
    @login_manager.user_loader
    def load_user(user_id):
        return User.objects(id=user_id).first()

# Flask views
@app.route('/')
def index():
    received = ReceiveLog.objects.all()
    return render_template(
        'index.html',
        user=login.current_user,
        received=received)


@app.route('/sent')
def sent():
    sent = SendLog.objects.all()
    return render_template('sent.html', user=login.current_user, sent=sent)


@app.route('/received')
def received():
    received = ReceiveLog.objects.all()
    return render_template(
        'received.html',
        user=login.current_user,
        received=received)

@app.route('/send_message', methods=('GET', 'POST'))
def send_message():
    if request.method == 'POST':
        for r in request.form.getlist("contact"):
            id = request.form.get('message[{}]'.format(r))
            message = Message.objects.get(id=id)
            new_message = {}
            contact = Contact.objects.get(id=r)
            today = datetime.datetime.now()
            if message.slug == 'mytrip':
                s = Template(message.message)
                s = s.safe_substitute(
                    name=contact.name,
                    status='ALL OK',
                    date=today.strftime('%Y-%m-%d'))
                new_message['body'] = str(s)
            else:
                new_message['body'] = str(message.message)
            log = SendLog()
            log.contact = contact
            log.message = message
            log.raw_message = new_message['body']
            log_id = log.save()
            new_message['number'] = contact.phone
            new_message['log'] = str(log.id)
            _redis.publish('message_ready', json.dumps(new_message))
            print new_message
        return redirect(url_for('index'))
    else:
        messages = Message.objects.all()
        contacts = Contact.objects.all()
        return render_template(
            'send_message.html',
            user=login.current_user,
            messages=messages,
            contacts=contacts)


@app.route('/login/', methods=('GET', 'POST'))
def login_view():
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = form.get_user()
        login.login_user(user)
        return redirect(url_for('index'))

    return render_template('form.html', form=form)


@app.route('/register/', methods=('GET', 'POST'))
def register_view():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        user = User()
        form.populate_obj(user)
        user.save()

        login.login_user(user)
        return redirect(url_for('index'))

    return render_template('form.html', form=form)


@app.route('/logout/')
def logout_view():
    login.logout_user()
    return redirect(url_for('index'))

#admin.add_view(UserView(User))
admin.add_view(ContactView(Contact))
admin.add_view(MessageView(Message))
admin.add_view(ModelView(SendLog))
admin.add_view(ModelView(ReceiveLog))

if __name__ == '__main__':
    init_login()
    app.run(host='0.0.0.0', debug=True)
