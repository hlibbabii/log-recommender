from math import log
from operator import itemgetter

from nn.params import nn_params

def combos(s, max_words=4):
    if not s:
        return
    yield (s,)
    if max_words == 1:
        return
    for i in range(1, len(s)):
        for c in combos(s[i:], max_words-1):
            yield (s[:i],) + c

dataset_name = nn_params["dataset_name"]
path_to_dataset = f'{nn_params["path_to_data"]}/{dataset_name}'

freqs = {}
with open(f'{path_to_dataset}/vocab.txt', 'r') as f:
    for l in f:
        line = l.split()
        freqs[line[0]] = int(line[1])

transformed = {}
for word, freq in freqs.items():
    denum = freq / log(len(word)+1) ** (0.25)
    options = []
    for subwords_set in combos(word):
        all_words_exist = True
        num = 0.0
        for subword in subwords_set:
            if subword in freqs:
                num += freqs[subword] * log(len(subword)+1) ** 4.0
            else:
                all_words_exist = False
        num = num / len(subwords_set)
        if all_words_exist:
            options.append((subwords_set, num, denum))
    options.sort(key=itemgetter(1), reverse=True)
    for option in options[:5]:
        result = option[1]/option[2]
        print(f'{option[0]} -> {word}: {option[1]}/{option[2]}={result}')
    if options[0][1]/options[0][2] > 50000 and len(options[0][0]) > 1:
        transformed[word] = options[0]
    print("================================")
print("#######################################")
with open(f'{path_to_dataset}/splitting.txt', 'w') as f:
    for word, tr in transformed.items():
        print(f'{word} --> {tr}')
        f.write(f'{word}|{" ".join(tr[0])}\n')
print(f"how many: {len(transformed)}")