import heapq, math

def build_graph(roads):
    g={}
    for r in roads:
        if r['status']!='open': continue
        c=float(r['distance'])*float(r.get('traffic',1))
        g.setdefault(r['from'],[]).append((r['to'],c)); g.setdefault(r['to'],[]).append((r['from'],c))
    return g

def astar(roads,start,goal):
    if start==goal: return {'path':[start],'cost':0.0}
    g=build_graph(roads); heap=[(0.0,0.0,start)]; came={}; score={start:0.0}; seen=set()
    while heap:
        _,cur_g,cur=heapq.heappop(heap)
        if cur in seen: continue
        seen.add(cur)
        if cur==goal:
            path=[cur]
            while cur in came: cur=came[cur]; path.append(cur)
            return {'path':path[::-1],'cost':round(cur_g,2)}
        for nxt,c in g.get(cur,[]):
            ng=cur_g+c
            if ng<score.get(nxt,math.inf):
                score[nxt]=ng; came[nxt]=cur; heapq.heappush(heap,(ng,ng,nxt))
    return None
