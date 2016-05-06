from dateutil import parser
from itsdangerous import TimestampSigner
from bson import json_util
from flask import flash, g, make_response, redirect, render_template, request, Response, url_for
from flask.ext import admin, login
from app import app
from admin_views import LoginForm
from models import IncomingMessages, OutgoingMessages, Message, Contact


# Flask views
@app.route('/')
def index():
    if not login.current_user.is_authenticated:
        return redirect(url_for('user_login'))
    received = IncomingMessages.objects.all()
    resp = make_response(render_template(
                         'index.html',
                         user=login.current_user,
                         received=received))
    # workaround for firefox issue with cookies
    if hasattr(g.user, 'id'):
        s = TimestampSigner(app.config["SECRET"])
        signature = s.sign(str(g.user.id))
        resp.set_cookie(app.config["OPERATOR_ID_COOKIE"], value=signature)
    return resp


@app.template_filter('format_date')
def _jinja2_filter_datetime(date, fmt=None):
    date = parser.parse(date)
    native = date.replace(tzinfo=None)
    format = '%d/%m/%Y %H:%M:%S'
    return native.strftime(format)


@app.route('/chats_history')
def chats_history():
    chats = {}
    contacts = IncomingMessages.objects.all().distinct("contact")
    for contact in contacts:
        incoming = list(IncomingMessages._get_collection().find({"contact": contact}))
        outgoing = list(OutgoingMessages._get_collection().find({"contact": contact}))
        conversation = incoming + outgoing
        conversation.sort(key=lambda chat: parser.parse(chat["created"]))
        chats[contact] = conversation
    return render_template('chats_history.html', chats=chats, user=login.current_user)


@app.route('/history')
def history():
    contact = request.args.get("contact")
    incoming = list(IncomingMessages._get_collection().find({"contact": contact}))
    outgoing = list(OutgoingMessages._get_collection().find({"contact": contact}))
    conversation = incoming + outgoing
    conversation.sort(key=lambda chat: parser.parse(chat["created"]))
    resp = Response(response=json_util.dumps({"conversation": conversation}),
                    status=200,
                    mimetype="application/json")
    return resp


@app.route('/get_clients_operator')
def get_clients_operator():
    outgoing = OutgoingMessages._get_collection().find({"operator_id": str(login.current_user.id)}).distinct("contact")
    resp = Response(response=json_util.dumps({"clients": outgoing}),
                    status=200,
                    mimetype="application/json")
    return resp


@app.route('/chats')
def chats():
    return render_template(
        'chats.html',
        user=login.current_user)


@app.route('/send_message', methods=('GET', 'POST'))
def send_message():
    if request.method == 'POST':
        pass
        # for r in request.form.getlist("contact"):
        #     id = request.form.get('message[{}]'.format(r))
        #     message = Message.objects.get(id=id)
        #     new_message = {}
        #     contact = Contact.objects.get(id=r)
        #     today = datetime.datetime.now()
        #     if message.slug == 'mytrip':
        #         s = Template(message.message)
        #         s = s.safe_substitute(
        #             name=contact.name,
        #             status='ALL OK',
        #             date=today.strftime('%Y-%m-%d'))
        #         new_message['body'] = str(s)
        #     else:
        #         new_message['body'] = str(message.message)
        #     log = SendLog()
        #     log.contact = contact
        #     log.message = message
        #     log.raw_message = new_message['body']
        #     log_id = log.save()
        #     new_message['number'] = contact.phone
        #     new_message['log'] = str(log.id)
        #     _redis.publish('message_ready', json.dumps(new_message))
        #     print new_message
        # return redirect(url_for('index'))
    else:
        contacts = list(IncomingMessages.objects.all().distinct("contact"))
        messages = Message.objects.all()
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
        flash('Logged in successfully.')
        s = TimestampSigner(app.config["SECRET"])
        signature = s.sign(user.get_id())
        next = request.args.get('next')
        # next_is_valid should check if the user has valid
        # permission to access the `next` url
        # if not next_is_valid(next):
        #    return flask.abort(400)
        redirect_to_index_or_next = redirect(next or url_for('chats'))
        response = app.make_response(redirect_to_index_or_next)
        response.set_cookie(app.config["OPERATOR_ID_COOKIE"], value=signature)
        return response
    return render_template('form.html', form=form)


@app.route('/logout/')
def logout_view():
    login.logout_user()
    return redirect(url_for('index'))
