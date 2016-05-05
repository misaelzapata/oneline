# -*- coding: utf-8 -*-
import json
import logging
import pika
from pymongo import MongoClient
from bson.objectid import ObjectId
from itsdangerous import TimestampSigner
from tornado.websocket import WebSocketHandler

from config import get_config
from constants import INCOMING_MESSAGES, OUTGOING_MESSAGES, PENDING_CLIENTS
from connections import db, pc_channel, om_channel

_CONF = 'DevelopmentConfig'  # TODO: Start using os env variables 
CONF = get_config(_CONF)
logging.basicConfig(format=CONF.LOGGING_FORMAT, level=CONF.LOGGING_LEVEL)


class SocketHandler(WebSocketHandler):
    def __init__(self, *args, **kwargs):
        self.OPERATORS = kwargs.pop('operators')
        self.CONTACTS = kwargs.pop('contacts')
        self.PASS_TO_OPERATOR = kwargs.pop('pass_to_operator')
        print kwargs
        super(SocketHandler, self).__init__(*args, **kwargs)

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
        if operator_id in self.OPERATORS:
            data = json.dumps({'type':'operator_new_session',
                'message':'Session closed: user connected on other terminal.'})
            self.OPERATORS[operator_id].write_message(data)
            self.OPERATORS[operator_id].close()
        # append to self.OPERATORS
        self.OPERATORS[operator_id] = self
        self._update_operators_status()

    def on_message(self, message):
        try:
            msg = json.loads(message)
            if msg['type'] == 'echo':
                self.write_message(u"You said: %s." % message)
            elif msg['type'] == 'listen_contact':
                operator_id = self._get_operator_id(self)
                self.CONTACTS[msg.contact] = operator_id
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
                self.OPERATORS[msg['to_operator_id']].write_message(dump)
                self.PASS_TO_OPERATOR[msg['contact']] = request
                logging.info('Request contact to operator response: %s' % \
                             request)
            elif msg['type'] == 'response_contact_request':
                logging.info('Response contact to operator: %s' % msg)
                if msg['contact'] not in self.PASS_TO_OPERATOR:
                    return
                request = self.PASS_TO_OPERATOR[msg['contact']]
                request['status'] = msg['status']
                if msg['status'] == 'accepted':
                    data = {'type':'new_client', 'contact':request['contact']}
                    dump = json.dumps(data)
                    logging.info('CONTACTS dump: %s' % self.ONTACTS)
                    if request['contact'] in self.CONTACTS:
                        del self.CONTACTS[request['contact']]
                    logging.info('CONTACTS dump again: %s' % self.CONTACTS)
                    self.OPERATORS[request['to_operator_id']].write_message(dump)
                dump = json.dumps(request)
                self.OPERATORS[request['from_operator_id']].write_message(dump)
                if msg['contact'] in self.PASS_TO_OPERATOR:
                    del self.PASS_TO_OPERATOR[msg['contact']]
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
        if operator_id in self.OPERATORS:
            self.OPERATORS.pop(operator_id)
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
            users_ids = map((lambda x: ObjectId(x)), self.OPERATORS.keys())
            users = db.user.find({'_id':{'$in':users_ids}})
            connected_users = map((lambda x: {'_id':str(x['_id']),
                                              'first_name':x['first_name'],
                                              'last_name':x['last_name']}),
                                  users)
            data = json.dumps({'type':'operators_status',
                               'connected':connected_users})
            for op in self.OPERATORS.values():
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
        self.CONTACTS[contact] = operator_id
        logging.info('CONTACTS dict updated:\n%s' % self.CONTACTS)