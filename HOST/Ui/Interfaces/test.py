"""
Test file -> delete later
"""
from Communication.protocol_layer.pl_core_communication import _RawMessage
import sys
from queue import Queue

list_test = [0xAA, 1, 0, 0, 4, 5, 4, 7, 8, 9, 10, 11, 12]
list_test = [0xAA, 1, 0, 0, 4, 5, 4, 7, 8, 9, 10, 11, 12]

liste_alles = []
liste_alles.append(list_test)
liste_alles.append(list_test)

neue_liste = liste_alles[0]

queue = Queue()
queue.put_nowait(liste_alles[0])
queue.put_nowait(liste_alles[0])
queue.put_nowait(liste_alles[0])
queue.put_nowait(liste_alles[0])
queue.put_nowait(liste_alles[0])




print("ende")
