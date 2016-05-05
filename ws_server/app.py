import json
import logging
import pika
import datetime
from bson.objectid import ObjectId
from pymongo import MongoClient
from tornado import websocket, web, ioloop
from itsdangerous import TimestampSigner

from config import get_config
from pika_consumer_thread import ConsumerWorkerThread
from constants import INCOMING_MESSAGES, OUTGOING_MESSAGES, PENDING_CLIENTS, \
    READED_MSG

# format {'operator_id':'websocket.WebSocketHandler'}
OPERATORS = {}
# format {'contact_jid':'operator_id'}
CONTACTS = {}
# 
PASS_TO_OPERATOR = {}

_CONF = 'DevelopmentConfig'  # TODO: Start using os env variables 
CONF = get_config(_CONF)
logging.basicConfig(format=CONF.LOGGING_FORMAT, level=CONF.LOGGING_LEVEL)

# MongoDB
client = MongoClient(host=CONF.MONGODB_HOST, port=CONF.MONGODB_PORT)
db = client[CONF.MONGODB_DB]

# RabbitMQ
rabbit_cn = pika.BlockingConnection(
    pika.ConnectionParameters(host=CONF.RABBITMQ_HOST))
# incoming messages
im_channel = rabbit_cn.channel()
im_channel.queue_declare(queue=INCOMING_MESSAGES, durable=True)
im_channel.basic_qos(prefetch_count=1)
# outgoing messages
om_channel = rabbit_cn.channel()
om_channel.queue_declare(queue=OUTGOING_MESSAGES, durable=True)
# pending clients
pc_channel = rabbit_cn.channel()
pc_channel.queue_declare(queue=PENDING_CLIENTS, durable=True)
pc_channel.basic_qos(prefetch_count=1)


class IndexHandler(web.RequestHandler):
    def get(self):
        s = TimestampSigner(CONF.SECRET)
        # test test test
        self.set_cookie(CONF.OPERATOR_ID_COOKIE,
                        s.sign('572a379621c9371635116447'))
        self.render("status.html")


class SocketHandler(websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        # check loggin
        operator_id = self._get_operator_id(self)
        if not operator_id:
            self.close()    
            return
        logging.info('Operator id %s connected.' % operator_id)
        # close previous session
        if operator_id in OPERATORS:
            data = json.dumps({'type':'operator_new_session',
                'message':'Session closed: user connected on other terminal.'})
            OPERATORS[operator_id].write_message(data)
            OPERATORS[operator_id].close()
        # append to OPERATORS
        OPERATORS[operator_id] = self
        self._update_operators_status()

    def on_message(self, message):
        try:
            msg = json.loads(message)
            if msg['type'] == 'echo':
                self.write_message(u"You said: %s." % message)
            elif msg['type'] == 'listen_contact':
                operator_id = self._get_operator_id(self)
                CONTACTS[msg.contact] = operator_id
            elif msg['type'] == 'response_to_contact':
                logging.info('Response to contact: %s' % msg)
                operator_id = self._get_operator_id(self)
                omsg = self._save_outgoing_message(msg, operator_id)
                if not omsg:
                    raise Exception('unable to save outgoing message %s' % msg)
                omsg['_id'] = str(omsg['_id'])
                om_channel.basic_publish(exchange='',
                                         routing_key=OUTGOING_MESSAGES,
                                         body=json.dumps(omsg),
                                         properties=pika.BasicProperties(
                                             delivery_mode = 2,
                                         ))
                logging.info('Outgoing message sent to queue.')
            elif msg['type'] == 'get_next_client':
                self._get_next_client(self)
            elif msg['type'] == 'request_contact_to_operator':
                logging.info('Request contact to operator: %s' % msg)
                request = {'type':'send_contact_request',
                           'contact':msg['contact'],
                           'from_operator_id':self._get_operator_id(self),
                           'to_operator_id':msg['to_operator_id'],
                           'status':'pending',
                           'message':msg['message']}
                dump = json.dumps(request)    
                OPERATORS[msg['to_operator_id']].write_message(dump)
                PASS_TO_OPERATOR[msg['contact']] = request
                logging.info('Request contact to operator response: %s' % \
                             request)
            elif msg['type'] == 'response_contact_request':
                logging.info('Response contact to operator: %s' % msg)
                request = PASS_TO_OPERATOR[msg['contact']]
                request['status'] = msg['status']
                if msg['status'] == 'accepted':
                    data = {'type':'new_client', 'contact':request['contact']}
                    dump = json.dumps(data)
                    logging.info('CONTACTS dump: %s' % CONTACTS)
                    if request['contact'] in CONTACTS:
                        CONTACTS[request['contact']].pop()
                    logging.info('CONTACTS dump again: %s' % CONTACTS)
                    OPERATORS[request['to_operator_id']].write_message(dump)
                dump = json.dumps(request)
                OPERATORS[request['from_operator_id']].write_message(dump)
                PASS_TO_OPERATOR.pop(msg['contact'])
                logging.info('Response contact to operator response: %s' % \
                             request)
            else:
                raise Exception('Wrong type.')
        except Exception as e:
            logging.error('Error receiving message: %s. Message: %s' % \
                          (e, message))
            data = json.dumps({'type':'request_failed',
                               'message':str(e),
                               'data':message})
            self.write_message(data)

    def on_close(self):
        # remove operator
        operator_id = self._get_operator_id(self)
        if operator_id in OPERATORS:
            OPERATORS.pop(operator_id)
        logging.info('Operator id %s disconnected.' % operator_id)
        # update operators status
        self._update_operators_status()

    def _get_operator_id(self, operator_cn):
        s = TimestampSigner(CONF.SECRET)
        try:
            cookie = operator_cn.get_cookie(CONF.OPERATOR_ID_COOKIE)
            if cookie is None:
                raise Exception('Cookie not found')
            operator_id = s.unsign(cookie, max_age=CONF.AUTH_EXPIRY)
            return operator_id
        except Exception as e:
            logging.error('Login error: %s.' % e)
            return False

    def _save_outgoing_message(self, msg, operator_id):
        try:
            omsg = {}
            omsg['contact'] = msg['contact']
            omsg['message'] = msg['message']
            omsg['sent'] = False
            omsg['operator_id'] = operator_id
            omsg['created'] = datetime.datetime.now().isoformat()
            result = db[OUTGOING_MESSAGES].insert_one(omsg)               
            logging.info('Outgoing message saved: %s' % omsg)
        except Exception as e:
            logging.error('Error saving outgoing message: %s.' % e)
            return False
        return omsg

    def _update_operators_status(self):
        try:
            users_ids = map((lambda x: ObjectId(x)), OPERATORS.keys())
            users = db.user.find({'_id':{'$in':users_ids}})
            connected_users = map((lambda x: {'_id':str(x['_id']),
                                              'first_name':x['first_name'],
                                              'last_name':x['last_name']}),
                                  users)
            data = json.dumps({'type':'operators_status',
                               'connected':connected_users})
            for op in OPERATORS.values():
                op.write_message(data)
            logging.info('Operator status updated: %s' % data)
        except Exception as e:
            logging.error('Error updating operators status: %s.' % e)

    def _get_next_client(self, operator):
        operator_id = self._get_operator_id(operator)
        logging.info('Getting next client to operator id %s.' % operator_id)
        method, header, body = pc_channel.basic_get(PENDING_CLIENTS)
        if body is None:
            raise Exception('No pending clients.')
            return
        logging.info('Got client: %s to operator id %s.' % (body, operator_id))
        operator.write_message(body)
        pc_channel.basic_ack(delivery_tag=method.delivery_tag)
        contact = json.loads(body)['contact']
        CONTACTS[contact] = operator_id
        logging.info('CONTACTS dict updated:\n%s' % CONTACTS)



def send_messages_to_operators(ch, method, properties, body):
    logging.info('New incoming message: %s.' % body)
    try:
        data = json.loads(body)
        contact = data['contact']
        msg_id = data['_id']
        if contact in CONTACTS:
            # send it to the assigned operator
            op_id = CONTACTS[contact]
            logging.info('Sending msg %s to operator %s.' % (msg_id, op_id))
            data['type'] = 'new_message'
            data = json.dumps(data)
            OPERATORS[op_id].write_message(data)
            # save the user and mark it as read
            update_sent_message(msg_id, op_id)
        else:
            # save into pending_clients
            data = {'type':'new_client', 'contact':contact}
            pc_channel.basic_publish(exchange='',
                                     routing_key=PENDING_CLIENTS,
                                     body=json.dumps(data),
                                     properties=pika.BasicProperties(
                                         delivery_mode = 2,
                                     ))
            # send alert to all operators
            send_new_message_alert()
            logging.info('Incoming mesage saved as pending.')        
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logging.error('An error ocurred while sending msg to client/s: %s' % e)

def send_new_message_alert():
    logging.info('Sending new msg alert to all operators.')
    msg_alert = '{"type":"new_message_alert"}'
    for op in OPERATORS.values():
        op.write_message(msg_alert)

def update_sent_message(msg_id, operator_id):
    try:
        result = db[INCOMING_MESSAGES].update_one(
            {"_id": ObjectId(msg_id)},
            {
                "$set": {
                    "user": ObjectId(operator_id),
                    "status": READED_MSG, 
                    "date_readed": datetime.datetime.now().isoformat()
                }
            }
        )
        logging.info('Incoming message id %s updated.' % msg_id)
    except Exception as e:
        logging.error('Error updating incomming message: %s.' % e)
        return False
    return result

app = web.Application([
    (r'/', IndexHandler),
    (r'/chat', SocketHandler),
])

if __name__ == '__main__':
    print """
 _      __      ____
| | /| / /__   / __/__ _____  _____ ____
| |/ |/ (_-<  _\ \/ -_) __/ |/ / -_) __/
|__/|__/___/ /___/\__/_/  |___/\__/_/
    """
    app.listen(CONF.PORT)
    logging.info('Listening on port: %s' % CONF.PORT)
    try:
        im_channel.basic_consume(send_messages_to_operators,
                                 queue=INCOMING_MESSAGES)
        im_thread = ConsumerWorkerThread(im_channel)
        im_thread.start()
        logging.info('Listening incoming messages queue.')
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        logging.info('Shutting down Ws Server...')
        ioloop.IOLoop.instance().stop()
        im_thread.stop()
        logging.info('Bye.')
