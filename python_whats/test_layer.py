from yowsup.layers.interface                           import YowInterfaceLayer, ProtocolEntityCallback
from yowsup.layers.protocol_messages.protocolentities  import TextMessageProtocolEntity
from pymongo import MongoClient
from bson.objectid import ObjectId
import json
import redis
import time

#config HERE
from config import DevConfig
c = DevConfig
##
from pymongo import MongoClient
client = MongoClient(host=c.MONGODB_HOST, port=c.MONGODB_PORT)
db = client[c.MONGODB_DB]


class TestLayer(YowInterfaceLayer):
    def __init__(self, transport = None):
        super(TestLayer, self).__init__()
        if transport:
            self.transport = transport
        self.name = 'redis'
        self.detached = False
        self.thread = False

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
    def print_this(self,item)        :
        data = json.loads(item['data'])
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
        
    def onEvent(self, layerEvent):
        #print layerEvent.getName()
        if layerEvent.getName() == 'start_redis':
            print 'redis started'
            client = redis.Redis(host=c.REDIS_HOST,port=c.REDIS_PORT)
            pubsub = client.pubsub()
            pubsub.subscribe(**{'message_ready': self.print_this})
            self.thread = pubsub.run_in_thread(sleep_time=0.001)
        if layerEvent.getName() == 'killredis':
            self.thread.stop()
    
    def isDetached(self):
        return self.detached

    def getName(self):
        return self.name        