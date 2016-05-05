import dateutil
import flask
from flask import request, render_template, url_for, redirect, make_response
from flask import Flask, g, flash
from flask.ext import admin, login
from itsdangerous import TimestampSigner
from dateutil import parser
from app import app
from models import *
from admin_views import LoginForm

# Flask views
@app.route('/')
def index():
    if not login.current_user.is_authenticated:
        return redirect(url_for('user_login'))
    received = IncomingMessage.objects.all()
    resp = make_response(render_template(
                         'index.html',
                         user=login.current_user,
                         received=received))
    ############### nigga stuff ###################
    if hasattr(g.user, 'id'):
        s = TimestampSigner(app.config["SECRET"])
        signature = s.sign(str(g.user.id))
        print '######### signature: %s #########' % signature
        resp.set_cookie(app.config["OPERATOR_ID_COOKIE"], value=signature)
    ############## end nigga stuff ################
    return resp


@app.template_filter('format_date')
def _jinja2_filter_datetime(date, fmt=None):
    date = dateutil.parser.parse(date)
    native = date.replace(tzinfo=None)
    format = '%d/%m/%Y %H:%M:%S'
    return native.strftime(format) 


@app.route('/chats_history')
def chats_history():
    from pymongo import MongoClient
    from flask import Response
    client = MongoClient(host=app.config["MONGODB_HOST"],
                         port=app.config["MONGODB_PORT"])
    dbz = client[app.config["MONGODB_DB"]]
    chats = {}
    contacts = dbz['incoming_messages'].distinct("contact")
    for contact in contacts:
        incoming = list(dbz['incoming_messages'].find({"contact": contact}))
        outgoing = list(dbz['outgoing_messages'].find({"contact": contact}))
        conversation = incoming + outgoing
        conversation.sort(key=lambda chat: parser.parse(chat["created"]))
        chats[contact] = conversation
    return render_template('chats.html', chats=chats)


@app.route('/history')
def history():
    # Feito :<
    from pymongo import MongoClient
    from flask import Response
    client = MongoClient(host='mongo', port=27017)
    dbz = client['oneline']
    contact = request.args.get("contact")
    incoming = list(dbz['incoming_messages'].find({"contact": contact}))
    outgoing = list(dbz['outgoing_messages'].find({"contact": contact}))
    from bson import json_util
    conversation = incoming + outgoing
    from dateutil import parser
    conversation.sort(key=lambda chat: parser.parse(chat["created"]))
    resp = Response(response=json_util.dumps({"conversation": conversation}),
                    status=200,
                    mimetype="application/json")
    return resp


@app.route('/get_clients_operator')
def get_clients_operator():
    # Feito :<
    from pymongo import MongoClient
    from flask import Response
    client = MongoClient(host='mongo', port=27017)
    dbz = client['oneline']
    outgoing = dbz['outgoing_messages'].distinct("contact", {"operator_id": str(login.current_user.id)})
    from bson import json_util
    resp = Response(response=json_util.dumps({"clients": outgoing}),
                    status=200,
                    mimetype="application/json")
    return resp


@app.route('/send_message')
def send_message():
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
        s = TimestampSigner(app.config["SECRET"])
        signature = s.sign(user.get_id())
        next = flask.request.args.get('next')
        # next_is_valid should check if the user has valid
        # permission to access the `next` url
        #if not next_is_valid(next):
        #    return flask.abort(400)
        redirect_to_index_or_next = redirect(next or flask.url_for('send_message'))
        response = app.make_response(redirect_to_index_or_next)
        response.set_cookie(app.config["OPERATOR_ID_COOKIE"], value=signature)
        return response
    return render_template('form.html', form=form)


@app.route('/logout/')
def logout_view():
    login.logout_user()
    return redirect(url_for('index'))
