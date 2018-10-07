# log-recommender

This is a project for a master thesis with a title "Supporting logging activities by mining software repositories"

## General Idea

The general idea is using a large number of projects from github to create a model 
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

### Data Gathering

### Data Preprocessing

#### Filtering out non-English projects

TODO: explain current algorithm

#### Tokenization

#### Basic splitting
Camel case and snake case splitting is done here

- camelCase -> camel case
- snake_case -> snake case
- splitting with numbers: cpp2java -> cpp 2 java
- number splitting: 123e-1 -> 1 2 3 <e> - 1

#### Same case splitting

samecasesplitting -> same case splitting

TODO: explain current algorithm

**Other approaches**: 

#### Typo Fixing
Misspelled words increase the vocabulary size and make code less understandable.

TODO: explain current algorithm

**Other approaches**: 

### Language model building

#### Improvements
##### Cache Component :heavy_check_mark:
##### Read input in 2 directions

### Applying language model to logging
- Sequence to sequence translation
- Retraining the last layers of language model to create a classifier 

### IntelliJ plugin building
** TBD **

## Implementation details
** TBD **
## Updating this README
** TBD **
