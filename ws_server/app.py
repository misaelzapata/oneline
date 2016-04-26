import json
import logging
import pika
from pymongo import MongoClient
from tornado import websocket, web, ioloop
from itsdangerous import TimestampSigner

from config import get_config
from pika_consumer_thread import ConsumerWorkerThread
from constants import INCOMING_MESSAGES

operators = []

_CONF = 'DevelopmentConfig'  # TODO: Start using os env variables 
CONF = get_config(_CONF)
logging.basicConfig(format=CONF.LOGGING_FORMAT, level=CONF.LOGGING_LEVEL)

# MongoDB
client = MongoClient(host=CONF.MONGODB_HOST, port=CONF.MONGODB_PORT)
db = client[CONF.MONGODB_DB]

# RabbitMQ
rabbit_cn = pika.BlockingConnection(
    pika.ConnectionParameters(host=CONF.RABBITMQ_HOST))
im_channel = rabbit_cn.channel()
im_channel.queue_declare(queue=INCOMING_MESSAGES, durable=True)
im_channel.basic_qos(prefetch_count=1)


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
        s = TimestampSigner(CONF.SECRET)
        try:
            cookie = self.get_cookie(CONF.OPERATOR_ID_COOKIE)
            if cookie is None:
                raise Exception('Cookie not found')
            operator_id = s.unsign(cookie, max_age=CONF.AUTH_EXPIRY)
            logging.info('Socket opened by User: %s' % operator_id)
        except Exception as e:
            logging.error('Loggin error: %s.' % e)
            self.close()    
            return
        # append to operators
        if self not in operators:
            self.contacts = []
            self.operator_id = operator_id
            operators.append(self)

    def on_message(self, message):
        try:
            msg = json.loads(message)
            # test test test
            if msg.type == 'echo':
                self.write_message(u"You said: %s." % message)
        except Exception as e:
            logging.error('Error receiving message: %s.' % e)

    def on_close(self):
        if self in operators:
            operators.remove(self)


def send_messages_to_operators(ch, method, properties, body):
    logging.info('New incoming message: %s.' % body)
    try:
        data = json.loads(body)
        # check if an operator is chatting with this contact
        operator = [x for x in operators if data['contact'] in x.contacts]
        data = json.dumps(data)
        if len(operator):
            op = operator[0]
            logging.info('Sending msg to operator %s.' % op.operator_id)
            op.write_message(data)
        else:
            logging.info('Sending msg all operators.')
            for c in operators:
                c.write_message(data)
        logging.info('Message sent succesfully, sending ACK to RabbitMQ.')        
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logging.error('An error ocurred while sending msg to client: %s' % e)

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
