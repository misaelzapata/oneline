import json
import logging
import pika
from pymongo import MongoClient
from tornado import websocket, web, ioloop
from itsdangerous import TimestampSigner

from config import get_config
from pika_consumer_thread import ConsumerWorkerThread
from constants import INCOMING_MESSAGES, OUTGOING_MESSAGES

# format {'operator_id':'websocket.WebSocketHandler'}
OPERATORS = {}
# format {'contact_jid':'operator_id'}
CONTACTS = {}

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


class IndexHandler(web.RequestHandler):
    def get(self):
        s = TimestampSigner(CONF.SECRET)
        # test test test
        self.set_cookie(CONF.OPERATOR_ID_COOKIE, s.sign('test123'))
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
        # append or update to OPERATORS
        # TODO: if already connected, alert and disconnect old client.
        OPERATORS[operator_id] = self

    def on_message(self, message):
        try:
            msg = json.loads(message)
            if msg.type == 'echo':
                # just for testing
                self.write_message(u"You said: %s." % message)
            elif msg.type == 'listen_contact':
                operator_id = self._get_operator_id(self)
                CONTACTS[msg.contact] = operator_id
                # update some mongo doc?
            elif msg.type == 'response_to_contact':
                omsg = {}
                omsg['contact'] = msg.contact
                omsg['message'] = msg.message
                omsg['sent'] = False
                result = db[OUTGOING_MESSAGES].insert_one(omsg)                
                omsg['_id'] = str(omsg['_id'])
                om_channel.basic_publish(exchange='',
                                         routing_key=OUTGOING_MESSAGES,
                                         body=json.dumps(omsg),
                                         properties=pika.BasicProperties(
                                             delivery_mode = 2,
                                         ))
            elif msg.type == 'pass_contact_to_operator':
                pass
        except Exception as e:
            logging.error('Error receiving message: %s.' % e)

    def on_close(self):
        # remove operator
        operator_id = self._get_operator_id(self)
        if operator_id in OPERATORS:
            OPERATORS.pop(operator_id)

    def _get_operator_id(self, operator_cn):
        s = TimestampSigner(CONF.SECRET)
        try:
            cookie = operator_cn.get_cookie(CONF.OPERATOR_ID_COOKIE)
            if cookie is None:
                raise Exception('Cookie not found')
            operator_id = s.unsign(cookie, max_age=CONF.AUTH_EXPIRY)
            return operator_id
        except Exception as e:
            logging.error('Loggin error: %s.' % e)
            return False


def send_messages_to_operators(ch, method, properties, body):
    logging.info('New incoming message: %s.' % body)
    try:
        data = json.loads(body)
        contact = data['contact']
        data = json.dumps(data)
        if contact in CONTACTS:
            # send it to the assigned operator
            op_id = CONTACTS[contact]
            logging.info('Sending msg to operator %s.' % op_id)
            OPERATORS[op_id].write_message(data)
        else:
            # send it to all operators
            logging.info('Sending msg all operators.')
            for op in OPERATORS.values():
                op.write_message(data)
        logging.info('Message forwarded succesfully, sending ACK to RabbitMQ.')        
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logging.error('An error ocurred while sending msg to client/s: %s' % e)

app = web.Application([
    (r'/', IndexHandler),
    (r'/chat', SocketHandler),
    (r'/(rest_api_example.png)', web.StaticFileHandler, {'path': '.'}),
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
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        logging.info('Shutting down Ws Server...')
        ioloop.IOLoop.instance().stop()
        im_thread.stop()
        logging.info('Bye.')
