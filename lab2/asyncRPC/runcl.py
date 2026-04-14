import time
import threading

import rpc
import logging

from context import lab_logging

lab_logging.setup(stream_level=logging.INFO)

def handleResult(result):
  print("Final result received:", result.value)

cl = rpc.Client()
cl.run()

base_list = rpc.DBList({'foo'})
thread = cl.append('bar', base_list, handleResult)

for i in range(10):
    print(f"Client is doing other work...")
    time.sleep(1)

thread.join()
cl.stop()
