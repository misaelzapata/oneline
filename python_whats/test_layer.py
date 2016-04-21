import json
import redis
import time
import thread
from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_messages.protocolentities  import TextMessageProtocolEntity
from pymongo import MongoClient
from bson.objectid import ObjectId

#config HERE
from config import DevConfig
c = DevConfig

# MongoDB
from pymongo import MongoClient
client = MongoClient(host=c.MONGODB_HOST, port=c.MONGODB_PORT)
db = client[c.MONGODB_DB]

# RabitMQ
import pika
from pika_consumer_thread import ConsumerWorkerThread
rabbit_cn = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))

class TestLayer(YowInterfaceLayer):
    def __init__(self, transport = None):
        super(TestLayer, self).__init__()
        if transport:
            self.transport = transport
        self.name = 'pika'
        self.detached = False
        self.om_thread = False

    def send_to_human(self,user, msg):
        #time.sleep( 1 )
        _msg = TextMessageProtocolEntity(
            msg.encode("UTF-8"),
            to=self.normalizeJid(user))        
        self.toLower(_msg)        
        print _msg

    #https://github.com/tgalal/yowsup/issues/475
    def normalizeJid(self, number):
        if '@' in number:
            return number

        return "%s@s.whatsapp.net" % number

    def om_callback(self, ch, method, properties, body):
        data = json.loads(body)
        print data
        self.send_to_human(data['number'],data['body'])
        result = db.send_log.update_one(
            {"_id": ObjectId(data['log'])},
            {
                "$set": {
                    "sent": 1
                }
            }
        )
        print result.matched_count
        print item 
        ch.basic_ack(delivery_tag = method.delivery_tag)
        
    def onEvent(self, layerEvent):
        #print layerEvent.getName()
        if layerEvent.getName() == 'start_pika':
            if not self.om_thread:
                self.om_channel = rabbit_cn.channel()
                self.om_channel.queue_declare(queue='outgoing_messages',
                                              durable=True)
                self.om_channel.basic_qos(prefetch_count=1)
                self.om_channel.basic_consume(self.om_callback, 
                                              queue='outgoing_messages')
                self.om_thread = ConsumerWorkerThread(self.om_channel)
                self.om_thread.start()
                print 'Pika thread started'
            else:
                print 'Pika thread already started'
        if layerEvent.getName() == 'kill_pika':
            if self.om_thread:
                self.om_thread.stop()
                print 'Pika thread stoped'
    
    def isDetached(self):
        return self.detached

    def getName(self):
        return self.name        


