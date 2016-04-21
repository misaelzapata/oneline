from yowsup.stacks import  YowStackBuilder

from incoming_layer_v1 import IncomingLayer
from outgoing_layer_v1 import OutgoingLayer

from yowsup.layers.auth import AuthError
from yowsup.layers import YowLayerEvent
from yowsup.layers.auth import YowAuthenticationProtocolLayer
from yowsup.layers.axolotl.layer import YowAxolotlLayer
import sys
import logging

from config import get_config


_CONF = 'DevelopmentConfig'  # TODO: Start using os env variables 
CREDENTIALS = get_config(_CONF).CREDENTIALS

class YowsupCliStack(object):
    def __init__(self, credentials, encryptionEnabled = True):
        stackBuilder = YowStackBuilder()
        self.thread = ''
        self.stack = stackBuilder\
            .pushDefaultLayers(encryptionEnabled)\
            .push(IncomingLayer)\
            .push(OutgoingLayer)\
            .build()

        self.stack.setCredentials(credentials)
        self.stack.setProp(YowAxolotlLayer.PROP_IDENTITY_AUTOTRUST, True)
    def start(self):
        self.stack.broadcastEvent(YowLayerEvent(IncomingLayer.EVENT_START))
        self.stack.broadcastEvent(YowLayerEvent('start_pika'))
        try:
            self.stack.loop(timeout = 0.5, discrete = 0.5)
        except AuthError as e:
            logging.info("Auth Error, reason {}".format(e))
        except KeyboardInterrupt:
            self.stack.broadcastEvent(OutgoingLayer('kill_pika'))
            self.stack.broadcastEvent(YowLayerEvent('kill_pika'))            
            print("\nOneLinedown")
            sys.exit(0)

if __name__==  "__main__":
    stack = YowsupCliStack(credentials=CREDENTIALS, encryptionEnabled=True)
    stack.start() #this is the program mainloop
