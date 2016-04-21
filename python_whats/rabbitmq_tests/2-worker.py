import pika
import time
import thread
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

connection = pika.BlockingConnection(pika.ConnectionParameters(host='localhost'))
channel = connection.channel()

channel.queue_declare(queue='task_queue', durable=True)
print(' [*] Waiting for messages. To exit press CTRL+C')

def callback(ch, method, properties, body):
    print(" [x] Received %r" % body)
    time.sleep(body.count(b'.'))
    print(" [x] Done")
    ch.basic_ack(delivery_tag = method.delivery_tag)

channel.basic_qos(prefetch_count=1)
channel.basic_consume(callback, queue='task_queue')

# channel_thread = thread.start_new_thread(channel.start_consuming, ())
# print channel_thread
# thread.start_new_thread(channel.start_consuming, ())
t = ConsumerWorkerThread(channel)
t.start()
print "is running!!!!!"
print "Chau en 10 seg...."
time.sleep(10)
t.stop()
print "kill thead."
# t.exit()
time.sleep(10)
