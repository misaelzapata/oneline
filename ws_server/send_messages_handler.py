# -*- coding: utf-8 -*-

"""
Author: Matias Bastos <matias.bastos@gmail.com>
"""

import datetime
import json
import logging
import pika
from bson.objectid import ObjectId
from tornado import web

from config import get_config
from connections import db, om_channel
from constants import OUTGOING_MESSAGES
from utils import get_operator_id

CONF = get_config()
logging.basicConfig(format=CONF.LOGGING_FORMAT, level=CONF.LOGGING_LEVEL)

class SendMessagesHandler(web.RequestHandler):
    # pylint: disable=W0223
    def post(self):
        # TODO: Use model objects.
        try:
            payload = json.loads(self.get_argument('payload'))
            operator_id = get_operator_id(self)
            logging.info('Sending bulk messages.')
            for msg in payload['messages']:
                if 'message_id' in msg:
                    message = db.message.find_one( \
                        {'_id':ObjectId(msg['message_id'])})
                    message = message['message']
                elif 'message' in msg:
                    message = msg['message']
                if not message:
                    raise Exception('Unable to get the message to send.')
                contact = db.contact.find_one(
                        {'_id':ObjectId(msg['contact_id'])})
                contact = contact['phone']
                omsg = self._save_outgoing_message(message, contact, operator_id)
                if not omsg:
                    raise Exception('Error saving outgoing message %s' % msg)
                omsg[u'_id'] = str(omsg['_id'])
                om_channel.basic_publish(exchange='',
                                         routing_key=OUTGOING_MESSAGES,
                                         body=json.dumps(omsg),
                                         properties=pika.BasicProperties(
                                             delivery_mode=2,
                                         ))
                logging.info('Outgoing message sent to queue.')
            logging.info('End sending bulk messages.')
        except Exception as error:
            logging.info('Not possible to send messages: %s', error)
        return

    @staticmethod
    def _save_outgoing_message(msg, contact, operator_id):
        try:
            omsg = {}
            omsg['contact'] = contact
            omsg['message'] = msg
            omsg['sent'] = False
            omsg['operator_id'] = operator_id
            omsg['created'] = datetime.datetime.now().isoformat()
            db[OUTGOING_MESSAGES].insert_one(omsg)
            logging.info('Outgoing message saved: %s', omsg)
        except Exception as error:
            logging.error('Error saving outgoing message: %s.', error)
            return False
        return omsg
