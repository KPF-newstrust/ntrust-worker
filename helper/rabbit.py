# -*- coding: utf-8 -*-
import logging
import pika

# Reference: http://pika.readthedocs.io/en/0.10.0/examples/asynchronous_consumer_example.html
# https://stackoverflow.com/questions/24510310/consume-multiple-queues-in-python-pika

NTRUST_QUEUE_NAME = "task"
NTRUST_EXCHANGE_NAME = "notice"

rb_connection = None

rb_notice_channel = None
rb_notice_queue_name = None
notice_consumer_tag = None

rb_task_channel = None
task_consumer_tag = None

is_stop_fired = False
last_uri = None

def user_notice_handler(body):
    print(" [N] %r" % body)

def user_task_handler(body):
    print(" [T] %r" % body)




def on_connection_open(connection):
    global rb_connection
    rb_connection = connection
    #print("[0] on_connection_open", connection)
    rb_connection.channel(on_notice_channel_open)
    rb_connection.channel(on_task_channel_open)
    rb_connection.add_on_close_callback(on_connection_closed)


def on_connection_closed(connection, reply_code, reply_text):
    #print("on_connection_closed:", connection, reply_code, reply_text)
    if is_stop_fired:
        connection.ioloop.stop()
    else:
        connection.add_timeout(3, _reconnect)

def _reconnect():
    print("AMQP: reconnect...")
    rb_connection.ioloop.stop()
    if last_uri:
        run(last_uri)

def on_notice_channel_open(channel):
    global rb_notice_channel
    #print("[N] on_notice_channel_open", channel)
    rb_notice_channel = channel
    rb_notice_channel.add_on_close_callback(on_notice_channel_closed)
    rb_notice_channel.exchange_declare(callback=on_notice_channel_declared,
                                       exchange=NTRUST_EXCHANGE_NAME, exchange_type='fanout')


def on_notice_channel_declared(frame):
    #print("[N] on_notice_channel_declared", frame)
    rb_notice_channel.queue_declare(on_notice_queue_declared, exclusive=True)


def on_notice_queue_declared(result):
    global rb_notice_queue_name
    #print("[N] on_notice_queue_declared", result)
    rb_notice_queue_name = result.method.queue
    rb_notice_channel.queue_bind(on_notice_queue_binded,
                                 exchange=NTRUST_EXCHANGE_NAME, queue=rb_notice_queue_name)


def on_notice_queue_binded(frame):
    global notice_consumer_tag
    #print("[N] on_notice_queue_binded", frame)
    notice_consumer_tag = rb_notice_channel.basic_consume(on_notice_consume, queue=rb_notice_queue_name, no_ack=True)


def on_notice_consume(ch, method, properties, body):
    user_notice_handler(body)


def on_notice_cancelok(frame):
    global notice_consumer_tag
    #print("[N] on_notice_cancelok")
    rb_notice_channel.close()
    notice_consumer_tag = None


def on_notice_channel_closed(channel, reply_code, reply_text):
    global rb_notice_channel
    #print("on_notice_channel_closed:", channel, reply_code, reply_text)
    rb_notice_channel = None
    check_shutdown()



def on_task_channel_open(channel):
    global rb_task_channel
    #print("[T] on_task_channel_open", channel)
    rb_task_channel = channel
    rb_task_channel.add_on_close_callback(on_task_channel_closed)
    rb_task_channel.queue_declare(on_task_queue_declared, queue=NTRUST_QUEUE_NAME, durable=True)


def on_task_queue_declared(result):
    #print("[T] on_task_queue_declared", result)
    rb_task_channel.basic_qos(on_task_basic_qosok, prefetch_count=1)


def on_task_basic_qosok(frame):
    global task_consumer_tag
    #print("[T] on_task_basic_qosok", frame)
    task_consumer_tag = rb_task_channel.basic_consume(on_task_consume, queue=NTRUST_QUEUE_NAME)


def on_task_consume(ch, method, properties, body):
    user_task_handler(body)
    ch.basic_ack(delivery_tag=method.delivery_tag)


def on_task_cancelok(frame):
    global task_consumer_tag
    #print("[T] on_task_cancelok", frame)
    rb_task_channel.close()
    task_consumer_tag = None


def on_task_channel_closed(channel, reply_code, reply_text):
    global rb_task_channel
    #print("on_task_channel_closed:", channel, reply_code, reply_text)
    rb_task_channel = None
    check_shutdown()



def run(uri):
    global last_uri
    last_uri = uri
    conn = pika.SelectConnection(parameters=pika.URLParameters(uri),
                                 on_open_callback=on_connection_open,
                                 stop_ioloop_on_close=False)
    conn.ioloop.start()


def stop():
    global is_stop_fired
    is_stop_fired = True
    last_uri = None

    if notice_consumer_tag != None:
        rb_notice_channel.basic_cancel(on_notice_cancelok, notice_consumer_tag)

    if task_consumer_tag != None:
        rb_task_channel.basic_cancel(on_task_cancelok, task_consumer_tag)

    rb_connection.ioloop.start()


def check_shutdown():
    if rb_notice_channel is None and rb_task_channel is None:
        rb_connection.close()



def set_notice_handler(handler):
    global user_notice_handler
    user_notice_handler = handler
    
    
def set_task_handler(handler):
    global user_task_handler
    user_task_handler = handler

