# -*- coding: utf-8 -*-
import logging
from tornado import web, ioloop
from itsdangerous import TimestampSigner

from config import get_config
from socket_handler import SocketHandler
from consumer_thread import ConsumerWorkerThread
from constants import INCOMING_MESSAGES
from incoming_messages_callback import send_messages_to_operators
from connections import im_channel

CONF = get_config()
logging.basicConfig(format=CONF.LOGGING_FORMAT, level=CONF.LOGGING_LEVEL)


class IndexHandler(web.RequestHandler):
    # pylint: disable=W0223
    def get(self):
        signer = TimestampSigner(CONF.SECRET)
        # test test test
        self.set_cookie(CONF.OPERATOR_ID_COOKIE,
                        signer.sign('572a379621c9371635116447'))
        self.render("status.html")


def run():
    # format {'operator_id':'websocket.WebSocketHandler'}
    operators = {}
    # format {'contact_jid':'operator_id'}
    contacts = {}
    # format
    pass_to_operator = {}
    try:
        # run incoming messages listener
        callback = lambda ch, method, properties, body: \
            send_messages_to_operators(ch,
                                       method,
                                       properties,
                                       body,
                                       operators=operators,
                                       contacts=contacts)
        im_channel.basic_consume(callback, queue=INCOMING_MESSAGES)
        im_thread = ConsumerWorkerThread(im_channel)
        im_thread.start()
        logging.info('Listening RabbitMQ incoming messages queue.')
        # run websocket server
        app = web.Application([
            (r'/', IndexHandler),
            (r'/chat', SocketHandler, {'operators':operators,
                                       'contacts':contacts,
                                       'pass_to_operator':pass_to_operator}),
        ])
        app.listen(CONF.PORT)
        logging.info('Listening on port: %s', CONF.PORT)
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        logging.info('Shutting down Ws Server...')
        ioloop.IOLoop.instance().stop()
        im_thread.stop()
        logging.info('Bye.')


if __name__ == '__main__':
    # pylint: disable=W1401
    print """
 _      __      ____
| | /| / /__   / __/__ _____  _____ ____
| |/ |/ (_-<  _\ \/ -_) __/ |/ / -_) __/
|__/|__/___/ /___/\__/_/  |___/\__/_/
    """
    run()
