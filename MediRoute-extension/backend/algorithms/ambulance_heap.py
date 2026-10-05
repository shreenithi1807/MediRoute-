import heapq
def best_ambulance(ambulances,scores):
    h=[(scores[a['id']],a['id'],a) for a in ambulances]; heapq.heapify(h)
    return heapq.heappop(h)[2] if h else None
