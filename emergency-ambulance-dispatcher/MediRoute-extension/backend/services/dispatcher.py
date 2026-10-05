from uuid import uuid4
from backend.services import data_service as ds
from backend.algorithms.astar import astar
from backend.algorithms.ambulance_heap import best_ambulance
from backend.algorithms.priority_queue import EmergencyPriorityQueue
queue=EmergencyPriorityQueue(); emergencies=[]
def create_emergency(location,emergency_type,severity,required_facility=''):
 e={'id':'E-'+uuid4().hex[:6].upper(),'location':location,'type':emergency_type,'severity':int(severity),'required_facility':required_facility,'status':'waiting'}; emergencies.append(e);queue.push(e);return e
def choose_ambulance(e):
 c=ds.available_ambulances(); scores={a['id']:(astar(ds.roads,a['location'],e['location']) or {'cost':10**9})['cost'] for a in c};return best_ambulance(c,scores)
def hscore(h,e):
 r=astar(ds.roads,e['location'],h['location'])
 if not r:return 10**9
 p=0
 if e['required_facility'].lower()=='icu' and not h['icu']:p+=1000
 if e['required_facility'].lower()=='trauma' and not h['trauma']:p+=1000
 if h['beds']<=0:p+=500
 return r['cost']+p
def dispatch(eid):
 e=next((x for x in emergencies if x['id']==eid),None)
 if not e: raise ValueError('Emergency not found')
 a=choose_ambulance(e)
 if not a:return {'success':False,'message':'No available ambulance.'}
 route=astar(ds.roads,a['location'],e['location'])
 if not route:return {'success':False,'message':'No route to emergency.'}
 hs=[h for h in ds.hospitals if h['beds']>0]; h=min(hs,key=lambda x:hscore(x,e),default=None)
 if not h:return {'success':False,'message':'No suitable hospital available.'}
 ds.update_ambulance(a['id'],status='dispatched');e['status']='dispatched'
 return {'success':True,'emergency':e,'ambulance':a,'route':route,'hospital':h,'eta_minutes':max(1,round(route['cost']*2))}
