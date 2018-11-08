from logrec.dataprep import base_project_dir
from logrec.dataprep.split.bpe_encode import read_merges, encode_word
from logrec.dataprep.split.samecase import manually_tagged_splittings_file_reader

path_manually_tagged_splittings = f'{base_project_dir}/manually_tagged_splittings.txt'
merges_file='/home/hlib/thesis/log-recommender/nn-data/devanbu_split_no_tabs_new_splits3_under_5000_15_percent/merges.txt'

stats, words_to_split = manually_tagged_splittings_file_reader.read(path_manually_tagged_splittings)

merges=read_merges(merges_file)
total_spl = len(stats['spl'])
success_spl=0
for orig, expected in stats['spl']:
    actual =" ".join(encode_word(orig, merges))
    if actual == expected:
        success_spl +=1
    else:
        print(f'{actual}  -- {expected}')

total_nonspl = len(stats['nonspl'])
success_nonspl=0
for expected in stats['nonspl']:
    actual =" ".join(encode_word(expected, merges))
    if actual == expected:
        success_nonspl +=1
    else:
        print(f'{actual}  ## {expected}')

print(f'Split: {success_spl} out of {total_spl}')
print(f'Nonsplit: {success_nonspl} out of {total_nonspl}')
print(f'Total: {success_nonspl + success_spl} out of {total_spl+total_nonspl}')