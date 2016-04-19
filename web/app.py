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
from flask.ext import admin, login
from flask.ext.admin import helpers

import flask_admin as flask_admin

from flask_debugtoolbar import DebugToolbarExtension


from models import Contact, Message, User, SendLog, ReceiveLog, \
    MyModelView, MyAdminIndexView, UserView, \
    ContactView, MessageView, \
    LoginForm, RegistrationForm

app = Flask(__name__)
app.config.from_object(DevConfig)
app.config['SECRET_KEY'] = '123456790'

app.config['DEBUG_TB_PANELS'] = [
    'flask.ext.mongoengine.panels.MongoDebugPanel']
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False
toolbar = DebugToolbarExtension(app)

# Create models
db = MongoEngine(app)

admin = Admin(app)

_redis = redis.StrictRedis(host='redis', port=6379)

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

admin.add_view(UserView(User))
admin.add_view(ContactView(Contact))
admin.add_view(MessageView(Message))
admin.add_view(ModelView(SendLog))
admin.add_view(ModelView(ReceiveLog))

if __name__ == '__main__':
    init_login()
    app.run(host='0.0.0.0', debug=True)
