# log-recommender

[![Build Status](https://travis-ci.org/hlibbabii/log-recommender.svg?branch=master)](https://travis-ci.org/hlibbabii/log-recommender)
[![Maintainability](https://api.codeclimate.com/v1/badges/09b85278219863d435c7/maintainability)](https://codeclimate.com/github/hlibbabii/log-recommender/maintainability)
[![Test Coverage](https://api.codeclimate.com/v1/badges/09b85278219863d435c7/test_coverage)](https://codeclimate.com/github/hlibbabii/log-recommender/test_coverage)

This is a project for a master thesis with a title "Supporting logging activities by mining software repositories"

# General Goal

The general goal is using a large number of projects from github to create a model 
that getting source code as input suggests different kind of information related to logging 
(e.g. place in code to put a logging statement, the text of the logging statement, log level etc.)

# Steps

## Data gathering
We use dataset from [Mining source code repositories at massive scale using language modeling. M Allamanis, C Sutton](https://dl.acm.org/citation.cfm?id=2487127)

**Statistics about dataset TBA**

[Data gathering](https://github.com/hlibbabii/log-recommender/wiki/1.-Data-gathering) in more details

## Data preprocessing

On this step data is prepared for the lang modelling step (tokenization, reduction of vocabulary size)

[Data preprocessing](https://github.com/hlibbabii/log-recommender/wiki/2.-Data-preprocessing) in more details

## Language modelling

Training language models using different kinds of architecture and different parameters; analysing and comparing performance of different models.


[Language modelling](https://github.com/hlibbabii/log-recommender/wiki/3.-Language-modelling) in more details

## Building classifier

Based on pretrained language model, we build classifiers that are trained to predict the correct position of log statement in the code, their level, text and variables in log statements.

[Building classifier](https://github.com/hlibbabii/log-recommender/wiki/4.-Building-classifier) in more details.

## IntelliJ plugin building

The pluggin supports developers by helping with log decisions.

[IntelliJ plugin building](https://github.com/hlibbabii/log-recommender-intellij-plugin) in more details.

# Supporting activities
- [log-recommender-cli](https://github.com/hlibbabii/log-recommender-cli): a command line tool for managing datasets
and their parsing, preprocessing etc.

# Implementation details

## Architecture and package overview in a nutshell
**TBA**
