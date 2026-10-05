from pathlib import Path
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel,Field
from backend.services import data_service as ds
from backend.services import dispatcher
from backend.algorithms.astar import astar
ROOT=Path(__file__).resolve().parents[1]
app=FastAPI(title='Emergency Ambulance Dispatcher')
app.add_middleware(CORSMiddleware,allow_origins=['*'],allow_methods=['*'],allow_headers=['*'])
app.mount('/static',StaticFiles(directory=ROOT/'frontend'),name='static')
class EmergencyIn(BaseModel):
 location:str; emergency_type:str='Accident'; severity:int=Field(5,ge=1,le=5); required_facility:str=''
class RoadUpdate(BaseModel): from_node:str;to_node:str;status:str
@app.get('/')
def home():return FileResponse(ROOT/'frontend/index.html')
@app.get('/api/state')
def state():return {'ambulances':ds.ambulances,'hospitals':ds.hospitals,'roads':ds.roads,'emergencies':dispatcher.emergencies}
@app.post('/api/reset')
def reset():ds.reset_data();dispatcher.emergencies.clear();dispatcher.queue=dispatcher.queue.__class__();return {'ok':True}
@app.post('/api/emergencies')
def add(e:EmergencyIn):return dispatcher.create_emergency(**e.model_dump())
@app.post('/api/dispatch/{eid}')
def dispatch(eid):
 try:return dispatcher.dispatch(eid)
 except ValueError as x:raise HTTPException(404,str(x))
@app.post('/api/roads')
def road(r:RoadUpdate):
 if not ds.update_road(r.from_node,r.to_node,r.status):raise HTTPException(404,'Road not found')
 return {'ok':True}
