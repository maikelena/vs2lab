import rpc
import logging
import threading
import time

from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)

cl = rpc.Client()
cl.run()

base_list = rpc.DBList({'foo'})
done = threading.Event()

#Callback 
def on_result(result_list):
    print("Result: {}".format(result_list.value))
    done.set()

# Starts call
cl.append_async('bar', base_list, on_result)

# Shows that active
while not done.is_set():
    print("Client is active while waiting...")
    time.sleep(1)

cl.stop()
