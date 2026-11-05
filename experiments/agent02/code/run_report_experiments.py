"""Additional measured experiments for the AGENT02 report.
Run from the report folder: MPLBACKEND=Agg python code/run_report_experiments.py
Original algorithms are imported unchanged from agent02_reference.py.
"""
from pathlib import Path
import sys, json, platform, csv
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import agent02_reference as ref

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / 'data'
IMG = ROOT / 'images'
DATA.mkdir(exist_ok=True)
IMG.mkdir(exist_ok=True)
plt.rcParams.update({'font.family':'DejaVu Sans','font.size':10,'axes.spines.top':False,'axes.spines.right':False,'figure.dpi':140})

config = ref.Config()
records=[]
curves={}

def run(label, config, seed, eval_seed, **kwargs):
    print('Training', label, 'seed', seed, flush=True)
    agent, train = ref.train_rl_against_rule(config, seed=seed, **kwargs)
    q_before = agent.q.copy()
    summary, episodes = ref.evaluate_pair(config, agent, seed=eval_seed)
    assert np.array_equal(q_before, agent.q), 'Evaluation changed Q table'
    ref.write_csv(DATA / f'{label}_training.csv', train)
    ref.write_csv(DATA / f'{label}_evaluation.csv', summary)
    ref.write_csv(DATA / f'{label}_evaluation_episodes.csv', episodes)
    ref.save_q_table(DATA / f'{label}_q.txt', agent)
    for s in summary:
        assert s['no_discount_actions']+s['discount_actions']==config.evaluation_episodes*config.steps_per_episode
        records.append(dict(experiment=label,train_seed=seed,evaluation_seed=eval_seed,discount=config.discount_rate,**s))
    curves[label]=train
    print(label, [(s['agent'],round(s['mean_reward_per_step'],4)) for s in summary], flush=True)
    return agent, train

# Reproduce the provided learning-rate experiment and retain its learning curves.
for a in [0.01,0.10,0.50]:
    run(f'alpha_{a:.2f}',config,1042,600042,alpha=a)
# Original 3 schedules plus the assignment's two suggested fixed schedules.
for name,start,minimum,decay in [('low',.05,.02,.999),('baseline',.20,.02,.995),('high',.50,.05,.995),('fixed005',.05,.05,1.),('fixed030',.30,.30,1.)]:
    run(f'exploration_{name}',config,2042,700042,epsilon_start=start,epsilon_min=minimum,epsilon_decay=decay)
# A controlled robustness modification: lower the discount from 20% to 5%.
# Same train and evaluation seed within each baseline/modified pair.
for seed in [11,22,33,44,55]:
    base_agent,_=run(f'robust_base_{seed}',config,seed,seed+800000)
    changed=ref.Config(discount_rate=.05)
    frozen=base_agent.q.copy()
    summary,_=ref.evaluate_pair(changed,base_agent,seed=seed+800000)
    assert np.array_equal(frozen,base_agent.q)
    for s in summary:
        records.append(dict(experiment=f'robust_frozen_{seed}',train_seed=seed,evaluation_seed=seed+800000,discount=.05,**s))
    run(f'robust_retrained_{seed}',changed,seed,seed+800000)
ref.write_csv(DATA/'all_evaluations.csv',records)

# Summary of training return, final-window return, and frozen evaluation.
training_summary=[]
for label,train in curves.items():
    evaluation=next(r for r in records if r['experiment']==label and r['agent']=='RL')
    training_summary.append(dict(experiment=label,training_mean=float(np.mean([r['rl_mean_reward_per_step'] for r in train])),first100=float(np.mean([r['rl_mean_reward_per_step'] for r in train[:100]])),last100=float(np.mean([r['rl_mean_reward_per_step'] for r in train[-100:]])),evaluation_mean=evaluation['mean_reward_per_step'],discount_rate=evaluation['discount_action_rate']))
ref.write_csv(DATA/'training_summary.csv',training_summary)

for prefix,title,filename in [('alpha_','Learning rate: training reward (100-episode windows)','learning_rate_curves.png'),('exploration_','Exploration: training reward (100-episode windows)','exploration_curves.png')]:
    fig,ax=plt.subplots(figsize=(9,4.5))
    for label,rows in curves.items():
        if label.startswith(prefix):
            values=np.array([r['rl_mean_reward_per_step'] for r in rows])
            ax.plot(np.arange(100,len(values)+1,100),values.reshape(-1,100).mean(axis=1),label=label.replace(prefix,''),linewidth=1.4)
    ax.set(xlabel='Training episode',ylabel='Mean profit per step',title=title)
    ax.grid(alpha=.2)
    ax.legend(ncol=3)
    fig.tight_layout();fig.savefig(IMG/filename);plt.close(fig)

summary=[]
for prefix,label in [('robust_base_','Baseline, discount 20%'),('robust_frozen_','Discount 5%, frozen policy'),('robust_retrained_','Discount 5%, retrained')]:
 for agent in ['RL','Rule-based']:
    rows=[r for r in records if r['experiment'].startswith(prefix) and r['agent']==agent]
    values=np.array([r['mean_reward_per_step'] for r in rows])
    summary.append(dict(condition=prefix,agent=agent,mean=float(values.mean()),std=float(values.std(ddof=1)),discount_rate=float(np.mean([r['discount_action_rate'] for r in rows])),n=len(rows)))
ref.write_csv(DATA/'robustness_summary.csv',summary)
fig,ax=plt.subplots(figsize=(9,4.5))
x=np.arange(3)
for agent,offset,color in [('RL',-.18,'#176b87'),('Rule-based',.18,'#df9940')]:
 rows=[r for r in summary if r['agent']==agent]
 ax.bar(x+offset,[r['mean'] for r in rows],.34,yerr=[r['std'] for r in rows],capsize=4,label=agent,color=color)
ax.set_xticks(x,['20% / baseline','5% / frozen RL','5% / retrained RL'])
ax.set(ylabel='Mean evaluation profit per step',title='Discount modification: mean and sample SD over 5 seeds')
ax.legend();ax.grid(axis='y',alpha=.2);fig.tight_layout();fig.savefig(IMG/'robustness.png');plt.close(fig)
metadata={'python':sys.version,'numpy':np.__version__,'matplotlib':matplotlib.__version__,'platform':platform.platform(),'config':vars(config),'seeds':[11,22,33,44,55],'evaluation_q_unchanged':True,'evaluation_action_counts_valid':True}
(DATA/'environment.json').write_text(json.dumps(metadata,indent=2))
print('DONE',json.dumps(summary,indent=2),flush=True)
