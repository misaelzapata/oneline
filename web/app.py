# app.py
from flask import Flask, g, flash
from config import BaseConfig, DevConfig
from flask.ext.mongoengine import MongoEngine
from flask.ext.security import Security, MongoEngineUserDatastore, \
    UserMixin, RoleMixin, login_required, utils, current_user

from flask.ext import admin, login
from flask_debugtoolbar import DebugToolbarExtension
from flask_security import utils

from models import User, Role, OutgoingMessage, IncomingMessage


app = Flask(__name__)
app.config.from_object(DevConfig)
app.config['SECRET_KEY'] = '123456790'

app.config['DEBUG_TB_PANELS'] = [
    'flask.ext.mongoengine.panels.MongoDebugPanel']
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
toolbar = DebugToolbarExtension(app)

# Create models
db = MongoEngine(app)

# Setup Flask-Security
user_datastore = MongoEngineUserDatastore(db, User, Role)
security = Security(app, user_datastore)

from views import *

# Create a user to test with
@app.before_first_request
def create_user():
    # Create the Roles "admin" and "end-user" -- unless they already exist
    user_datastore.find_or_create_role(name='admin', description='Administrator')
    user_datastore.find_or_create_role(name='operator', description='Operator')

    # Create two Users for testing purposes -- unless they already exists.
    # In each case, use Flask-Security utility function to encrypt the password.
    encrypted_password = utils.encrypt_password('admin')
    if not user_datastore.get_user('dropkek@oneline.net'):
        user_datastore.create_user(email='dropkek@oneline.net', password=encrypted_password, username="a",
                                   first_name="a", last_name="b")
    encrypted_password = utils.encrypt_password('123456')
    if not user_datastore.get_user('operator@oneline.net'):
        user_datastore.create_user(email='operator@oneline.net', password=encrypted_password, username="b",
                                   first_name="b", last_name="c")

    user_datastore.add_role_to_user('dropkek@oneline.net', 'admin')
    user_datastore.add_role_to_user('operator@oneline.net', 'operator')
    if not user_datastore.get_user('mzapata@droptek.com'):
        user_datastore.create_user(email='mzapata@droptek.com', password=encrypted_password, username="misael",
                                   first_name="Misael", last_name="Zapata")
    user_datastore.add_role_to_user('mzapata@droptek.com', 'admin')
                                   
    if not user_datastore.get_user('mbastos@droptek.com'):
        user_datastore.create_user(email='mbastos@droptek.com', password=encrypted_password, username="matias",
                                   first_name="Matias", last_name="Bastos")
    user_datastore.add_role_to_user('mbastos@droptek.com', 'operator')
    
    if not user_datastore.get_user('fapelhanz@droptek.com'):
        user_datastore.create_user(email='fapelhanz@droptek.com', password=encrypted_password, username="federico",
                                   first_name="Federico", last_name="Apenhanz")
    user_datastore.add_role_to_user('fapelhanz@droptek.com', 'operator')
    
# Views
from admin_views import *

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


if __name__ == '__main__':
    init_login()
    app.run(host='0.0.0.0', debug=True)
