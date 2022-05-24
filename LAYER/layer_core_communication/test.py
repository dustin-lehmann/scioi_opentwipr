import queue
import core_messages

msg = core_messages.SetLEDMessage(1,1)

Queue = queue.Queue()

Queue.put(msg)

msg2 = Queue.get(msg)

while (0<0):
    print("ende")

print("ende 2")
