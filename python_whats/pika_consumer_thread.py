import threading

class ConsumerWorkerThread(threading.Thread):
    def __init__(self, channel):
        super(ConsumerWorkerThread, self).__init__()
        self.channel = channel
        self._running = False

    def run(self):
        if self._running:
            return
        self._running = True
        while self._running:
            self.channel.connection.process_data_events(time_limit=1)

    def stop(self):
        self._running = False
        self.channel.stop_consuming()
