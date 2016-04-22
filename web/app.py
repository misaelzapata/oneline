# app.py
import json
import datetime
import redis
from string import Template
import flask
from flask import Flask, g, flash
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

from wtforms import form, fields, validators
from wtforms.fields import PasswordField
from flask.ext.admin import helpers, expose

from models import Contact, Message, User, Role, SendLog, ReceiveLog, \
    MyModelView, UserView, \
    ContactView, MessageView

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
        return User.objects(email=self.login.data).first()


class RegistrationForm(form.Form):
    login = fields.TextField(validators=[validators.required()])
    email = fields.TextField()
    password = fields.PasswordField(validators=[validators.required()])

    def validate_login(self, field):
        if db.session.query(User).filter_by(login=self.login.data).count() > 0:
            raise validators.ValidationError('Duplicate username')

# Customized admin views

class MyAdminIndexView(admin.AdminIndexView):

    @expose('/')
    def index(self):
        if not login.current_user.is_authenticated:
            return redirect(url_for('.login_view'))
        return super(MyAdminIndexView, self).index()

    @expose('/login/', methods=('GET', 'POST'))
    def login_view(self):
        # handle user login

        form = LoginForm(request.form)
        if request.method == 'POST' and form.validate():
            user = User.objects(username=form.username.data).first()
            if user is not None:
                print user.password
                print form.password.data
                if user and verify_password(form.password.data, user.password):
                    login.login_user(user)
                    flash("Logged in successfully!", category='success')
                return redirect(url_for('admin.index'))
            flash("Wrong username or password!", category='error')

        if login.current_user.is_authenticated:
            return redirect(url_for('.index'))
        link = '<p>Don\'t have an account? <a href="' + \
            url_for('.register_view') + '">Click here to register.</a></p>'
        self._template_args['form'] = form
        self._template_args['link'] = link
        return super(MyAdminIndexView, self).index()

    @expose('/register/', methods=('GET', 'POST'))
    def register_view(self):
        form = RegistrationForm(request.form)
        if helpers.validate_form_on_submit(form):
            user = User()

            form.populate_obj(user)
            # we hash the users password to avoid saving it as plaintext in the db,
            # remove to use plain text:
            user.password = generate_password_hash(form.password.data)

            db.session.add(user)
            db.session.commit()

            login.login_user(user)
            return redirect(url_for('.index'))
        link = '<p>Already have an account? <a href="' + \
            url_for('.login_view') + '">Click here to log in.</a></p>'
        self._template_args['form'] = form
        self._template_args['link'] = link
        return super(MyAdminIndexView, self).index()

    @expose('/logout/')
    def logout_view(self):
        login.logout_user()
        return redirect(url_for('.index'))
        
class UserView(ModelView):

    def is_accessible(self):
        return login.current_user.is_authenticated

    #column_filters = ['first_name', 'last_name', 'username']
    #column_exclude_list = ['password', ]
    #form_excluded_columns = ('password',)
    #column_searchable_list = ('first_name', 'password')

    #form_overrides = dict(password=PasswordField)
    # On the form for creating or editing a User, don't display a field corresponding to the model's password field.
    # There are two reasons for this. First, we want to encrypt the password before storing in the database. Second,
    # we want to use a password field (with the input masked) rather than a
    # regular text field.
    def scaffold_form(self):

        # Start with the standard form as provided by Flask-Admin. We've already told Flask-Admin to exclude the
        # password field from this form.
        form_class = super(UserView, self).scaffold_form()

        # Add a password field, naming it "password2" and labeling it "New
        # Password".
        form_class.password2 = PasswordField('New Password')
        return form_class

    # This callback executes when the user saves changes to a newly-created or edited User -- before the changes are
    # committed to the database.
    def on_model_change(self, form, model, is_created):

        # If the password field isn't blank...
        if len(model.password2):

            # ... then encrypt the new password prior to storing it in the database. If the password field is blank,
            # the existing password in the database will be retained.
            model.password = model.password2

# Customized admin views


class RoleView(ModelView):

    def is_accessible(self):
        return login.current_user.is_authenticated

    column_filters = ['name']

# Create customized model view class

class MyModelView(ModelView):

    def is_accessible(self):
        return login.current_user.is_authenticated

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
    encrypted_password = utils.encrypt_password('admin')
    if not user_datastore.get_user('dropkek@oneline.net'):
        user_datastore.create_user(email='dropkek@oneline.net', password=encrypted_password)

# Views

# Initialize Flask-Admin
admin = admin.Admin(
    app,
    'Admin',
    index_view=MyAdminIndexView())
# Add Flask-Admin views for Users and Roles
admin.add_view(ModelView(User))
admin.add_view(ModelView(Role))
# ADMIN #

@app.before_request
def before_request():
    g.user = current_user
# Initialize flask-login
def init_login():
    login_manager = login.LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = "user_login"
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



@app.route('/login/', methods=['GET', 'POST'])
def user_login():
    # Here we use a class of some kind to represent and validate our
    # client-side form data. For example, WTForms is a library that will
    # handle this for us, and we use a custom LoginForm to validate.
    form = LoginForm(request.form)
    if request.method == 'POST' and form.validate():
        user = form.get_user()
        login.login_user(user)
        flask.flash('Logged in successfully.')

        next = flask.request.args.get('next')
        # next_is_valid should check if the user has valid
        # permission to access the `next` url
        #if not next_is_valid(next):
        #    return flask.abort(400)

        return redirect(next or flask.url_for('index'))
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
