"""Render actual released cell estimates and Wilson intervals into a PNG."""
import json
from pathlib import Path
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt

ROOT=Path(__file__).resolve().parents[1]
summary=json.loads((ROOT/'results/v01_summary.json').read_text())
models=list(summary['models']);cards=['0w','50w','150w','400w']
colors=['#263746','#428a8e','#d29845','#9c6377']
fig,axes=plt.subplots(1,2,figsize=(13,6.2))
fig.patch.set_facecolor('#faf9f6')
labels={'claude-opus-5-5':'Claude Opus 5.5','claude-sonnet-5':'Claude Sonnet 5','claude-haiku-4-5-20251001':'Claude Haiku 4.5','gpt-6-astra':'GPT 6 Astra','gpt-6.1-sol':'GPT 6.1 Sol'}
for ax,metric,title in zip(axes,['UHR','TUR'],['Unforced harm among completed trajectories','Task completion across all scheduled trajectories']):
    ax.set_facecolor('#faf9f6')
    for j,card in enumerate(cards):
        points=[]
        for i,model in enumerate(models):
            cell=summary['models'][model]['cards'][card];rate=cell[metric]
            val=rate['estimate']
            if val is None:continue
            low,high=rate['wilson_95'];y=i+(j-1.5)*.16
            ax.errorbar(val*100,y,xerr=[[max(0,(val-low)*100)],[max(0,(high-val)*100)]],fmt='o',color=colors[j],capsize=3,markersize=5,label=card if i==0 else None)
    ax.set(yticks=range(len(models)),yticklabels=[labels.get(m,m) for m in models],xlim=(-3,103),xlabel='Percent',title=title)
    ax.invert_yaxis();ax.grid(axis='x',color='#deded8',linewidth=.7)
    for side in ['top','right','left']:ax.spines[side].set_visible(False)
    ax.tick_params(axis='y',length=0,pad=12)
from matplotlib.lines import Line2D
axes[0].legend(handles=[Line2D([0],[0],marker='o',color=c,label=k) for c,k in zip(colors,cards)],frameon=False,ncol=4,loc='lower left',bbox_to_anchor=(0,-.27))
fig.suptitle('Welfare State Evals v0.1',x=.06,ha='left',fontsize=23,fontweight='bold')
fig.text(.06,.88,f"{summary['recorded_trajectories']} recorded trajectories. Five models. Four policy lengths. Thirty operational environments.",fontsize=11,color='#555555')
fig.text(.06,.055,'Intervals: analytic Wilson 95%. Provider errors and refusals count against task completion.\nSDOR is undefined in a cell with no harmful completions. Yan Su <hi@yansu.me>.',fontsize=9,color='#555555')
fig.subplots_adjust(left=.17,right=.97,top=.77,bottom=.27,wspace=.65)
fig.savefig(ROOT/'results/summary.png',dpi=180,facecolor=fig.get_facecolor())
plt.close(fig)
print('results/summary.png')
