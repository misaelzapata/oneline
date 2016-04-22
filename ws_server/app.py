import json
import logging
import pika
from pymongo import MongoClient
from tornado import websocket, web, ioloop

from config import get_config
from pika_consumer_thread import ConsumerWorkerThread
from constants import INCOMING_MESSAGES

clients = []

_CONF = 'DevelopmentConfig'  # TODO: Start using os env variables 
CONF = get_config(_CONF)
logger = logging.getLogger(__name__)

# MongoDB
# client = MongoClient(host=c.MONGODB_HOST, port=c.MONGODB_PORT)
# db = client[c.MONGODB_DB]

# RabbitMQ
rabbit_cn = pika.BlockingConnection(
    pika.ConnectionParameters(host=CONF.RABBITMQ_HOST))
im_channel = rabbit_cn.channel()
im_channel.queue_declare(queue=INCOMING_MESSAGES, durable=True)
im_channel.basic_qos(prefetch_count=1)


class IndexHandler(web.RequestHandler):
    def get(self):
        self.render("status.html")


class SocketHandler(websocket.WebSocketHandler):
    def check_origin(self, origin):
        return True

    def open(self):
        if self not in clients:
            clients.append(self)

    def on_close(self):
        if self in clients:
            clients.remove(self)


class ApiHandler(web.RequestHandler):

    @web.asynchronous
    def get(self, *args):
        self.finish()
        id = self.get_argument("id")
        value = self.get_argument("value")
        data = {"id": id, "value" : value}
        data = json.dumps(data)
        for c in clients:
            c.write_message(data)

    @web.asynchronous
    def post(self):
        pass


app = web.Application([
    (r'/', IndexHandler),
    (r'/ws', SocketHandler),
    (r'/api', ApiHandler),
    (r'/(rest_api_example.png)', web.StaticFileHandler, {'path': '.'}),
])

def send_to_clients(ch, method, properties, body):
    print('new message: ', body)
    data = json.loads(body)
    data = {"id": 2, "value" : data['message']}
    data = json.dumps(data)
    for c in clients:
        c.write_message(data)
    ch.basic_ack(delivery_tag=method.delivery_tag)


if __name__ == '__main__':
    print """
  _      __      ____
 | | /| / /__   / __/__ _____  _____ ____
 | |/ |/ (_-<  _\ \/ -_) __/ |/ / -_) __/
 |__/|__/___/ /___/\__/_/  |___/\__/_/

 Listening on port: 8080
    """
    app.listen(8080)
    try:
        im_channel.basic_consume(send_to_clients, queue=INCOMING_MESSAGES)
        im_thread = ConsumerWorkerThread(im_channel)
        im_thread.start()
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        print '\nShutting down Ws Server...'
        ioloop.IOLoop.instance().stop()
        im_thread.stop()
        print '\nBye.'
