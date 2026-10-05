import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from mcp.server import MCPServer
from backend.services import data_service as ds
from backend.services import dispatcher
from backend.algorithms.astar import astar
mcp=MCPServer('Emergency Ambulance Dispatcher',instructions='Educational simulator only; never claim real emergency services were contacted.')
@mcp.tool()
def get_available_ambulances()->list:'''Return available simulated ambulances.''';return ds.available_ambulances()
@mcp.tool()
def get_emergencies()->list:'''Return simulated emergencies.''';return dispatcher.emergencies
@mcp.tool()
def get_hospitals()->list:'''Return simulated hospital capacity and facilities.''';return ds.hospitals
@mcp.tool()
def get_traffic_conditions()->list:'''Return traffic-weighted road status.''';return ds.roads
@mcp.tool()
def calculate_route(start:str,goal:str)->dict:'''Calculate a traffic-weighted route.''';return astar(ds.roads,start,goal) or {'error':'No route available'}
@mcp.tool()
def create_emergency(location:str,emergency_type:str,severity:int,required_facility:str='')->dict:'''Create and prioritize a simulated emergency.''';return dispatcher.create_emergency(location,emergency_type,severity,required_facility)
@mcp.tool()
def dispatch_ambulance(emergency_id:str)->dict:'''Dispatch the best available simulated ambulance.''';return dispatcher.dispatch(emergency_id)
@mcp.tool()
def block_road(from_node:str,to_node:str)->dict:'''Block a simulated road for rerouting demonstration.''';return {'ok':ds.update_road(from_node,to_node,'blocked')}
@mcp.tool()
def open_road(from_node:str,to_node:str)->dict:'''Reopen a simulated road.''';return {'ok':ds.update_road(from_node,to_node,'open')}
if __name__=='__main__':mcp.run(transport='stdio')
