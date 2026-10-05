from backend.algorithms.astar import astar
from backend.algorithms.priority_queue import EmergencyPriorityQueue
from backend.algorithms.ambulance_heap import best_ambulance
def test_astar():
 r=astar([{'from':'A','to':'B','distance':2,'traffic':1,'status':'open'},{'from':'B','to':'C','distance':2,'traffic':1,'status':'open'}],'A','C');assert r['path']==['A','B','C']
def test_priority():
 q=EmergencyPriorityQueue();q.push({'id':'low','severity':2});q.push({'id':'critical','severity':5});assert q.pop()['id']=='critical'
def test_heap():assert best_ambulance([{'id':'A1'},{'id':'A2'}],{'A1':5,'A2':2})['id']=='A2'
