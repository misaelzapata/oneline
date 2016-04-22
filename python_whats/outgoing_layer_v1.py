# -*- coding: utf-8 -*-

import json
import pika
from bson.objectid import ObjectId
from pymongo import MongoClient
from yowsup.layers.interface import YowInterfaceLayer
from yowsup.layers.protocol_messages.protocolentities import TextMessageProtocolEntity
from pika_consumer_thread import ConsumerWorkerThread

from config import get_config
from constants import OUTGOING_MESSAGES


_CONF = 'DevelopmentConfig'  # TODO: Start using os env variables


class OutgoingLayer(YowInterfaceLayer):
    def __init__(self, transport=None):
        super(OutgoingLayer, self).__init__()
        if transport:
            self.transport = transport
        self.name = 'pika'
        self.detached = False
        self.om_thread = False
        # get config
        self.conf = get_config(_CONF)
        # connect to mongodb
        client = MongoClient(host=self.conf.MONGODB_HOST,
                             port=self.conf.MONGODB_PORT)
        self.db = client[self.conf.MONGODB_DB]
        # connect to rabbit
        rabbit_cn = pika.BlockingConnection(
            pika.ConnectionParameters(host='localhost'))
        self.om_channel = rabbit_cn.channel()
        self.om_channel.queue_declare(queue=OUTGOING_MESSAGES, durable=True)
        self.om_channel.basic_qos(prefetch_count=1)
        self.om_channel.basic_consume(self.on_message_callback,
                                      queue=OUTGOING_MESSAGES)

    def send_message(self, user, msg):
        _msg = TextMessageProtocolEntity(msg.encode("UTF-8"),
                                         to=self.normalize_jid(user))
        self.toLower(_msg)
        print _msg

    def normalize_jid(self, number):
        if '@' in number:
            return number
        return "%s@s.whatsapp.net" % number

    def on_message_callback(self, ch, method, properties, body):
        data = json.loads(body)
        print data
        self.send_message(data['user'], data['message'])
        result = self.db.send_log.update_one(
            {"_id": ObjectId(data['log'])},
            {
                "$set": {
                    "sent": 1
                }
            }
        )
        ch.basic_ack(delivery_tag=method.delivery_tag)
        print result.matched_count

    def onEvent(self, layerEvent):
        #print layerEvent.getName()
        if layerEvent.getName() == 'start_pika':
            if not self.om_thread:
                self.om_thread = ConsumerWorkerThread(self.om_channel)
                self.om_thread.start()
                print 'Pika thread started.'
            else:
                print 'Pika thread already started.'
        if layerEvent.getName() == 'kill_pika':
            if self.om_thread:
                self.om_thread.stop()
                print 'Pika thread stoped'

    def isDetached(self):
        return self.detached

    def getName(self):
        return self.name
