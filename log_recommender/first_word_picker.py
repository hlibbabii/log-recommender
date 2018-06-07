import argparse
import csv
import pickle
from random import shuffle
import time

from pybrain import SoftmaxLayer
from pybrain.datasets import ClassificationDataSet
from pybrain.supervised import BackpropTrainer
from pybrain.tools.shortcuts import buildNetwork
from pybrain.utilities import percentError
from io_utils import load_classes
import io_utils


def get_label_by_class(cl, classes):
    return classes.index(cl)

def test_nn(logs_for_testing, classes, context_lines_to_consider, verbose=False):
    ranks = []
    top_3_count= 0
    top_5_count= 0
    for log in logs_for_testing:
        vector = [w in log.get_context_words(context_lines_to_consider) for w in interesting_words_from_context]
        result = net.activate(vector)
        sorted_result = sorted(enumerate(result),key=lambda x: x[1], reverse=True)
        class_label = get_label_by_class(log.first_word_cathegory, classes)
        rank_of_guess = list(map(lambda x: x[0], sorted_result)).index(class_label)
        if rank_of_guess <= 2:
            top_3_count += 1
        if rank_of_guess <= 4:
            top_5_count += 1
        if verbose:
            print(log.get_context_words(context_lines_to_consider))
            print("Chosen " + str(sorted_result[0][0]) + " " + str(classes[sorted_result[0][0]]) + " with probability " + str(sorted_result[0][1]))
            print("Chosen " + str(sorted_result[1][0]) + " " + str(classes[sorted_result[1][0]]) + " with probability " + str(sorted_result[1][1]))
            # print("Chosen " + str(sorted_result[2][0]) + " " + str(classes[sorted_result[2][0]]) + " with probability " + str(sorted_result[2][1]))
            print("Rank of guess: " + str(rank_of_guess))

            print(", but was: " + log.first_word_cathegory)
        ranks.append(rank_of_guess)
    return sum(ranks) / len(ranks), top_3_count / len(ranks), top_5_count / len(ranks)


def createDataSet(interesting_words_from_context, classes, n_hidden_layers, logs, context_lines_to_consider):
    n_input_nodes = len(interesting_words_from_context)
    n_output_nodes = len(classes)
    dataset = ClassificationDataSet(n_input_nodes, n_hidden_layers, nb_classes=n_output_nodes)
    for log in logs:
        vector = [w in log.get_context_words(context_lines_to_consider) for w in interesting_words_from_context]

        expected_class_label = get_label_by_class(log.first_word_cathegory, classes)
        dataset.addSample(vector, [expected_class_label])
    dataset._convertToOneOfMany()
    return dataset


def split_into_two(lst, part):
    shuffle(lst)
    div_point = int(len(lst) * part)
    return lst[:div_point], lst[div_point:]


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--min-word-occurencies', action='store', type=int, default=2000)
    args = parser.parse_args()

    major_classes_logs = io_utils.load_major_classes_logs()

    # preprocessed_logs = preprocessed_logs[:2000]
    classes = load_classes()

    interesting_words_from_context = io_utils.load_interesting_words()

    logs_for_testing, logs_for_training = split_into_two(major_classes_logs, 0.25)

    n_input_nodes = len(interesting_words_from_context)
    n_output_nodes = len(classes)
    n_hidden_layers = 1
    n_hidden_nodes = (n_input_nodes + n_output_nodes) // 2

    trndata = createDataSet(interesting_words_from_context, classes, n_hidden_layers, logs_for_training)
    tstdata = createDataSet(interesting_words_from_context, classes, n_hidden_layers, logs_for_testing)

    print("Number of training patterns: ", len(trndata))
    print("Input and output dimensions: ", trndata.indim, trndata.outdim)
    print("First sample (input, target, class):")
    print(trndata['input'][0], trndata['target'][0], trndata['class'][0], logs_for_training[0].first_word_cathegory)

    net = buildNetwork(trndata.indim, n_hidden_nodes, trndata.outdim, outclass=SoftmaxLayer)

    trainer = BackpropTrainer( net, dataset=trndata, momentum=0.1, verbose=True, weightdecay=0.01)
    for i in range(1):
        start_time = time.time()
        trainer.trainEpochs(1)
        time_for_training = time.time() - start_time
        trnresult = percentError( trainer.testOnClassData(), trndata['class'] )
        tstresult = percentError( trainer.testOnClassData(dataset=tstdata ), tstdata['class'] )

        average_rank, percent_in_3_top, percent_in_5_top = test_nn(logs_for_testing[::len(logs_for_testing) // 15], classes, verbose=True)

        print("Training took " + str(time_for_training) + " seconds.")
        print("epoch: %4d" % trainer.totalepochs, "  train error: %5.2f%%" % trnresult, "  test error: %5.2f%%" % tstresult)
        print("Average rank: " + str(average_rank))
        print("Top 3 guess percent: " + str(percent_in_3_top))
        print("Top 5 guess percent: " + str(percent_in_5_top))



# test data - use a separate proj for testing
# remove OTHER class
# make nn to identify the exact word
# after that stemmed word,
# do clustering to identify 'similar' first words
# group 'similar' first words and rerun classification
# same amount of test data for different classes

