import heapq
class EmergencyPriorityQueue:
    def __init__(self): self.h=[]; self.seq=0
    def push(self,e):
        self.seq+=1; heapq.heappush(self.h,(6-int(e['severity']),self.seq,e))
    def pop(self): return heapq.heappop(self.h)[2] if self.h else None
    def peek(self): return self.h[0][2] if self.h else None
    def items(self): return [x[2] for x in sorted(self.h)]
