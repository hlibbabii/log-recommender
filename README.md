# log-recommender

[![Build Status](https://travis-ci.org/hlibbabii/log-recommender.svg?branch=master)](https://travis-ci.org/hlibbabii/log-recommender)
[![Maintainability](https://api.codeclimate.com/v1/badges/09b85278219863d435c7/maintainability)](https://codeclimate.com/github/hlibbabii/log-recommender/maintainability)

This is a project for a master thesis with a title "Supporting logging activities by mining software repositories"

## General Goal

The general goal is using a large number of projects from github to create a model 
that getting source code as input suggests different kind of information related to logging 
(e.g. place in code to put a logging statement, the text of the logging statement, log level etc.)

## Steps
- [Data gathering](#data-gathering)
- [Data preprocessing](#data-preprocessing)
- [Language model building](#language-model-building)
- [Classifier building](#applying-language-model-to-logging)
- [IntelliJ plugin building](intellij-plugin-building)

**Supporting activities:**
- [log-recommender-cli](https://github.com/hlibbabii/log-recommender-cli): a command line tool for managing datasets 
and their parsing, preprocessing etc.

## Data Gathering
14,317 projects from Github
[Mining source code repositories at massive scale using language modeling. M Allamanis, C Sutton](https://dl.acm.org/citation.cfm?id=2487127)

## Data Preprocessing

#### Filtering out non-English files and replacing remaining non-English words with a placeholder

Files that contain more non-English words than a certain threshold are removed (This threshould is different for identifiers, comments, string literals). The thresholds are identified empirically.
In the files that remained, non-English words are replaced with a <non-English> placeholder. Blocks of non-English text are replacedc with a <non-eng-contents> placeholder, e.g. in comments or strign literals

The world is non-English if:

- it is not found in the English dictionaries **AND**
- It is found in at least one of Non-English Dictionaries **AND**
- It has more than 3 letters

**OR**

- It contains Unicode characters (At the moment for simplicity words like *Café* and *Naїve* are considered non-English)

##### Dictionaries Used:
**TBD**

#### Tokenization
**TBD**

#### Basic splitting
Splitting using a few trivial algorithms

- `camelCase` -> `camel case`
- `snake_case` -> `snake case`
- splitting with numbers: `cpp2java` -> `cpp 2 java`
- number splitting: `123e-1` -> `1 2 3 <e> - 1`

#### Same case splitting

`samecasesplitting` -> `same case splitting` 

Currently, a heuristic that chooses a splitting amoung the set of all possible splittings is uded. The heuristic favours splittings with the following properties: 
- resulting subwords should occur individually as often as possible in the dataset
- the length of the subwords should be close to the average length of words in vocabulary (~ 5 in our case) with more penalty for shorter words

##### Steps

1. The vocabulary of alamanis dataset is calculated as following
```shell
`lorec vocab build en_100_percent 1101001`
```
- camelcase and undercase splitting is done
- splitting of numerals is done
- string and comments are NOT removed
- non-English words are removed

```shell

cat /home/lv71161/hlibbabii/log-recommender/nn-data/new_framework/en_100_percent/metadata/1101111/vocab | grep  "^[a-z]\+ [0-9]\+$" > /home/lv71161/hlibbabii/log-recommender/vocab
```

1. The resulting vocabulary is used as input file (`{base_project_dir}/vocab`) to splitting algorithm (`logrec/split/samecase/splitter.py`)

```shell
python logrec/dataprep/split/samecase/splitter.py
```

1. The algorithm produces `splitting.txt` file.

1. Parsing-preprocessing framework uses `splitting.txt` for splitting

Related papers:
[Splitting source code identifiers using Bidirectional LSTM Recurrent Neural Network](https://arxiv.org/abs/1805.11651)
- check this approach against our manually tagged data (manually_tagged_splittings.txt).


#### Typo Fixing
Misspelled words also increase the vocabulary size.

Currently done based on the heuristic used for same case splitting as well as Levenstein dsitance between a word and possible fixes.

Related papers: 
**TBD**

#### Data preprocessing improvements (ordered by priority)
- Resolving unicode decode errors [(Issue link)](https://github.com/hlibbabii/log-recommender/issues/15)
- Consider words like *Café* and *Naїve* English [(Issue link)](https://github.com/hlibbabii/log-recommender/issues/16)

## Language model building

-Experimenting with params :heavy_check_mark:

#### Improvements
##### Cache Component :heavy_check_mark:
##### Read input in 2 directions

## Applying language model to logging
- Sequence to sequence translation
- Retraining the last layers of language model to create a classifier

**Questions**:

- Do we need to modify our language at all? It should have learned logging already.
- Do we need to preprocess log statement somehow during parsing, to make it easier for the model to be trained (the way log-extractor worked)

## IntelliJ plugin building
**TBD**

## Implementation details
**TBD**
