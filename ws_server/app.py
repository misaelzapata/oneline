import json
import logging
import datetime
from tornado import web, ioloop
from itsdangerous import TimestampSigner

from config import get_config
from socket_handler import SocketHandler
from consumer_thread import ConsumerWorkerThread
from constants import INCOMING_MESSAGES, OUTGOING_MESSAGES, PENDING_CLIENTS, \
    READED_MSG
from incoming_messages_callback import send_messages_to_operators
from connections import im_channel

_CONF = 'DevelopmentConfig'  # TODO: Start using os env variables 
CONF = get_config(_CONF)
logging.basicConfig(format=CONF.LOGGING_FORMAT, level=CONF.LOGGING_LEVEL)


# format {'operator_id':'websocket.WebSocketHandler'}
OPERATORS = {}
# format {'contact_jid':'operator_id'}
CONTACTS = {}
# 
PASS_TO_OPERATOR = {}


class IndexHandler(web.RequestHandler):
    def get(self):
        s = TimestampSigner(CONF.SECRET)
        # test test test
        self.set_cookie(CONF.OPERATOR_ID_COOKIE,
                        s.sign('572a379621c9371635116447'))
        self.render("status.html")


app = web.Application([
    (r'/', IndexHandler),
    (r'/chat', SocketHandler, {'operators':OPERATORS,
                               'contacts':CONTACTS,
                               'pass_to_operator':PASS_TO_OPERATOR}),
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
        callback = lambda ch, method, properties, body: \
            send_messages_to_operators(ch,
                                       method,
                                       properties,
                                       body,
                                       operators=OPERATORS,
                                       contacts=CONTACTS)
        im_channel.basic_consume(callback, queue=INCOMING_MESSAGES)
        im_thread = ConsumerWorkerThread(im_channel)
        im_thread.start()
        logging.info('Listening incoming messages queue.')
        ioloop.IOLoop.instance().start()
    except KeyboardInterrupt:
        logging.info('Shutting down Ws Server...')
        ioloop.IOLoop.instance().stop()
        im_thread.stop()
        logging.info('Bye.')
