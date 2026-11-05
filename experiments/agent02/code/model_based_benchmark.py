"""Known-model finite-horizon planning benchmark; not a learned agent.
State: (time, demand, own previous action, opponent previous action).
Undiscounted profit objective matches the evaluation metric.
"""
from pathlib import Path
import numpy as np
import agent02_reference as ref

class PlanningAgent:
    def __init__(self, config):
        self.config=config
        H=config.steps_per_episode
        self.values=np.zeros((H+1,2,2,2))
        self.policy=np.zeros((H,2,2,2),dtype=int)
        for t in range(H-1,-1,-1):
            for d in range(2):
                for own_prev in range(2):
                    for other_prev in range(2):
                        other_action=int(d==1 and own_prev==1)
                        scores=[]
                        for a in range(2):
                            n=config.low_demand_customers if d==0 else config.high_demand_customers
                            p=float(np.clip(.30+.25*d+.15*a-.10*other_action,.05,.95))
                            immediate=n*p*(config.price*(1-config.discount_rate*a)-config.unit_cost)
                            future=.5*(self.values[t+1,0,a,other_action]+self.values[t+1,1,a,other_action])
                            scores.append(immediate+future)
                        self.values[t,d,own_prev,other_prev]=max(scores)
                        self.policy[t,d,own_prev,other_prev]=int(np.argmax(scores))
        self.t=0
        self.own_prev=0

    def act(self, state, explore=False):
        if self.t==0:
            self.own_prev=0
        d,other_prev=state
        action=int(self.policy[self.t,d,self.own_prev,other_prev])
        self.own_prev=action
        self.t=(self.t+1)%self.config.steps_per_episode
        return action

    def expected_mean(self):
        return float(.5*(self.values[0,0,0,0]+self.values[0,1,0,0])/self.config.steps_per_episode)

def main():
    root=Path(__file__).resolve().parents[1]
    rows=[]
    for delta in [.20,.05]:
        config=ref.Config(discount_rate=delta)
        for seed in [11,22,33,44,55]:
            agent=PlanningAgent(config)
            result,_=ref.evaluate_pair(config,agent,seed=seed+800000)
            for r in result:
                rows.append(dict(delta=delta,seed=seed,policy='Planning' if r['agent']=='RL' else 'Rule-based',expected_planning_mean=agent.expected_mean(),**{k:v for k,v in r.items() if k!='agent'}))
    ref.write_csv(root/'data/planning_benchmark.csv',rows)
    for delta in [.20,.05]:
        subset=[r for r in rows if r['delta']==delta and r['policy']=='Planning']
        vals=[r['mean_reward_per_step'] for r in subset]
        print(delta,'expected',subset[0]['expected_planning_mean'],'observed mean',np.mean(vals),'SD',np.std(vals,ddof=1),'discount rate',np.mean([r['discount_action_rate'] for r in subset]))
if __name__=='__main__':main()
