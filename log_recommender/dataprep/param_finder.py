from dataprep import base_project_dir
from dataprep.lcsplitting.param_mutator import ParamMutator

file160 = f'{base_project_dir}/160.json'

import json

with open(file160) as f:
    tagged_files = json.load(f)

total = len(tagged_files)
noneng = sum([i['noneng'] for i in tagged_files])
eng = total - noneng

possibel_var_values, (keys, mutations) = ParamMutator(
    [{'name': 'code_percent', 'start': 0.005, 'end': 0.05, 'plus_or_mult': 'plus', 'koef': 0.0005},
     {'name': 'code_non_eng', 'start': 2.01, 'end': 60, 'plus_or_mult': 'mult', 'koef': 1.4},
     {'name': 'code_non_eng_uq', 'start': 2.01, 'end': 30, 'plus_or_mult': 'mult', 'koef': 1.5},
     {'name': 'code_str_percent', 'start': 0.005, 'end': 0.05, 'plus_or_mult': 'plus', 'koef': 0.0005},
     {'name': 'code_str_non_eng', 'start': 2.01, 'end': 60, 'plus_or_mult': 'mult', 'koef': 1.4},
     {'name': 'code_str_non_eng_uq', 'start': 2.01, 'end': 30, 'plus_or_mult': 'mult', 'koef': 1.4}]) \
    .mutate(2000000, 5)


def metric(code_percent, code_non_eng, code_non_eng_uq, code_str_percent, code_str_non_eng, code_str_non_eng_uq):
    count_good = 0
    count_bad = 0
    for file in tagged_files:
        if (file['code_percent'] >= code_percent and file['code_non_eng'] >= code_non_eng and file[
            'code_non_eng_uq'] >= code_non_eng_uq) or (
                file['code_str_percent'] >= code_str_percent and file['code_str_non_eng'] >= code_str_non_eng and file[
            'code_str_non_eng_uq'] >= code_str_non_eng_uq):
            if file['noneng']:
                count_good += 1
            else:
                count_bad += 1
    precision = float(count_good) / (count_good + count_bad) if (count_good + count_bad) > 0 else 0
    recall = float(count_good) / noneng
    return precision * 5 / 10 + recall * 5 / 10, precision, recall


results = []
for mutation in mutations:
    val, prec, recall = metric(*mutation)
    results.append({'params': mutation, 'metric': val, 'prec': prec, 'recall': recall})

sorted_results = sorted(results, key=lambda x: x['metric'], reverse=True)

for sorted_result in sorted_results[:100]:
    print(sorted_result)

# Results of a few runs
# {'params': (0.006, 2.01, 2.01, 0.019, 3.939599999999999, 2.01), 'metric': 0.933664996420902, 'prec': 0.84251968503937, 'recall': 0.9727272727272728}
# {'params': (0.0075, 2.8139999999999996, 4.522499999999999, 0.0195, 2.01, 2.01), 'metric': 0.9158249158249158, 'prec': 0.9259259259259259, 'recall': 0.9090909090909091}
# {'params': (0.007, 5.515439999999998, 4.522499999999999, 0.0185, 2.01, 2.8139999999999996), 'metric': 0.9175084175084174, 'prec': 0.9259259259259259, 'recall': 0.9090909090909091}
