# -*- coding: utf-8 -*-
import json
import logging
import pika
import datetime
from bson.objectid import ObjectId

from config import get_config
from constants import PENDING_CLIENTS,INCOMING_MESSAGES, READED_MSG
from connections import db, pc_channel 

_CONF = 'DevelopmentConfig'  # TODO: Start using os env variables 
CONF = get_config(_CONF)
logging.basicConfig(format=CONF.LOGGING_FORMAT, level=CONF.LOGGING_LEVEL)


def send_messages_to_operators(ch, method, properties, body,
                               operators, contacts):
    logging.info('New incoming message: %s.' % body)
    try:
        data = json.loads(body)
        contact = data['contact']
        msg_id = data['_id']
        if contact in contacts:
            # send it to the assigned operator
            op_id = contacts[contact]
            logging.info('Sending msg %s to operator %s.' % (msg_id, op_id))
            data['type'] = 'new_message'
            data = json.dumps(data)
            operators[op_id].write_message(data)
            # save the user and mark it as read
            _update_sent_message(msg_id, op_id)
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
            _send_new_message_alert(operators)
            logging.info('Incoming mesage saved as pending.')        
        ch.basic_ack(delivery_tag=method.delivery_tag)
    except Exception as e:
        logging.error('An error ocurred while sending msg to client/s: %s' % e)

def _send_new_message_alert(operators):
    logging.info('Sending new msg alert to all operators.')
    msg_alert = '{"type":"new_message_alert"}'
    for op in operators.values():
        op.write_message(msg_alert)

def _update_sent_message(msg_id, operator_id):
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
