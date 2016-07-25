from yowsup.stacks import  YowStackBuilder
from layer import EchoLayer
from yowsup.layers.auth import AuthError
from yowsup.layers import YowLayerEvent
from yowsup.layers.network import YowNetworkLayer
from yowsup.layers.axolotl.layer import YowAxolotlLayer
from incoming_layer_v1 import IncomingLayer
from outgoing_layer_v1 import OutgoingLayer

class YowsupStack(object):
    def __init__(self, credentials, encryptionEnabled = True):
        stackBuilder = YowStackBuilder()

        self.stack = stackBuilder\
            .pushDefaultLayers(encryptionEnabled)\
            .push(IncomingLayer)\
            .push(OutgoingLayer)\
            .build()

        self.stack.setCredentials(credentials)
        self.stack.setProp(YowAxolotlLayer.PROP_IDENTITY_AUTOTRUST, True)

    def start(self):
        self.stack.broadcastEvent(YowLayerEvent(YowNetworkLayer.EVENT_STATE_CONNECT))
        self.stack.broadcastEvent(YowLayerEvent('start_pika'))
        try:
            self.stack.loop()
        except AuthError as e:
            print("Authentication Error: %s" % e.message)
        except KeyboardInterrupt:
            self.stack.broadcastEvent(OutgoingLayer('kill_pika'))
            self.stack.broadcastEvent(YowLayerEvent('kill_pika'))
            print("\nOneLinedown")
            sys.exit(0)
if __name__ == "__main__":
    print """
  ____           __   _
 / __ \___  ___ / /  (_)__  ___
/ /_/ / _ \/ -_) /__/ / _ \/ -_)
\____/_//_/\__/____/_/_//_/\__/

    """
    CREDENTIALS = ('5215549998261','ms4h0xO9KDL/jTo3VHd0B5v1z0I=')
    stack = YowsupStack(credentials=CREDENTIALS, encryptionEnabled=True)
    stack.start() #this is the program mainloop
