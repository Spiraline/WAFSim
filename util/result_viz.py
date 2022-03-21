from os import listdir
import matplotlib.pyplot as plt

WAF_dict = {'Greedy': [], 'CB': [], 'LCCB': []}
GC_dict = {'Greedy': [], 'CB': [], 'LCCB': []}
trace_arr = []

for file in listdir('res'):
    policy = file.split('-')[0]
    trace = file.split('-')[2]
    tag = file.split('-')[3]
    if trace not in trace_arr:
        trace_arr.append(trace)
    with open('res/' + file, 'r') as f:
        res = f.readline().strip().split(',')
        GC_count = int(res[1])
        WAF = float(res[2])
        WAF_dict[policy].append(WAF)
        GC_dict[policy].append(GC_count)

print('Trace\tGreedy\t\tCB\t\tLC-CB')
for idx, trace in enumerate(trace_arr):
    print('%s\t(%4d %7.3f)\t(%4d %7.3f)\t(%4d %7.3f)'
        % (trace,
        GC_dict['Greedy'][idx],
        WAF_dict['Greedy'][idx],
        GC_dict['CB'][idx],
        WAF_dict['CB'][idx],
        GC_dict['LCCB'][idx],
        WAF_dict['LCCB'][idx]))
        
    # print(WAF_dict['LCCB'][idx] / WAF_dict['Greedy'][idx] * 100)
    # print(WAF_dict['LCCB'][idx] / WAF_dict['CB'][idx] * 100)

# Visualize
fig, ax = plt.subplots(figsize=(20, 7))
plt.subplots_adjust(left=0.05, right=0.95, top=0.9, bottom=0.1)
plt.rcParams['font.size'] = 15

axis_list = [i*1.5 for i in range(0, len(trace_arr))]

plt.bar([i-0.3 for i in axis_list], WAF_dict['Greedy'], label='Greedy', align='center', width=0.3, color='white', edgecolor='black')
plt.bar([i for i in axis_list], WAF_dict['CB'], label='CB', align='center', width=0.3, color='gray', edgecolor='black')
plt.bar([i+0.3 for i in axis_list], WAF_dict['LCCB'], label='LC-CB', align='center', width=0.3, color='white', edgecolor='black', hatch='///')
plt.legend()
plt.xticks(fontsize=8)

ax.set_xlabel('MSRC Trace', fontsize=13)
ax.set_ylabel('WA', fontsize=13)
# ax.set_title('Failure by method and density')

plt.xticks(axis_list, trace_arr)

plt.savefig('res.eps', format='eps')
plt.savefig('res.png')

plt.show()