from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]; DATA=ROOT/'data'
def load(n): return json.loads((DATA/n).read_text())
ambulances=load('ambulances.json'); hospitals=load('hospitals.json'); roads=load('roads.json')
def reset_data():
 global ambulances,hospitals,roads
 ambulances,hospitals,roads=load('ambulances.json'),load('hospitals.json'),load('roads.json')
def available_ambulances(): return [a for a in ambulances if a['status']=='available']
def get_ambulance(i): return next((a for a in ambulances if a['id']==i),None)
def update_ambulance(i,**kw):
 a=get_ambulance(i)
 if a:a.update(kw)
 return a
def update_road(a,b,status):
 ok=False
 for r in roads:
  if {r['from'],r['to']}=={a,b}:r['status']=status;ok=True
 return ok
