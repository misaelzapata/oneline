# -*- coding: utf-8 -*-
import pika
from pymongo import MongoClient

from config import get_config
from constants import INCOMING_MESSAGES, OUTGOING_MESSAGES, PENDING_CLIENTS

_CONF = 'DevelopmentConfig'  # TODO: Start using os env variables 
CONF = get_config(_CONF)


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
