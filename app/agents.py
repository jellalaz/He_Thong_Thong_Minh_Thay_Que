from dataclasses import dataclass,field
from typing import Callable,Any
@dataclass
class Message:
 sender:str
 receiver:str
 type:str
 content:Any
@dataclass
class Agent:
 name:str
 handler:Callable
 memory:dict=field(default_factory=dict)
 def receive(self,message,bus):
  self.memory['calls']=self.memory.get('calls',0)+1
  self.memory['last_request']=message.type
  return self.handler(message.content,bus)
class MessageBus:
 def __init__(self):self.agents={};self.trace=[]
 def register(self,agent):self.agents[agent.name]=agent
 def request(self,sender,receiver,content,kind='REQUEST'):
  self.trace.append(vars(Message(sender,receiver,kind, str(content) if isinstance(content,dict) and 'x' in content else content)))
  try:
   result=self.agents[receiver].receive(Message(sender,receiver,kind,content),self)
   self.trace.append(vars(Message(receiver,sender,'INFORM',result.tolist() if hasattr(result,'tolist') else result)))
   return result
  except Exception as exc:
   self.trace.append(vars(Message(receiver,sender,'FAILURE',type(exc).__name__)))
   raise
