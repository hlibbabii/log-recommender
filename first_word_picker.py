import argparse
import pickle
from random import shuffle
from pybrain import SoftmaxLayer
from pybrain.datasets import ClassificationDataSet
from pybrain.supervised import BackpropTrainer
from pybrain.tools.shortcuts import buildNetwork
from pybrain.utilities import percentError
import time
from freqs import calc_frequency_stats, \
    classify_logs_by_first_word, get_word_frequences, get_significant_words


def get_interesting_words_from_logs(log, interesting_words_from_context):
    return [value for value in log.context_words if value in interesting_words_from_context]


def build_vector(found_words, interesting_words):
    return [w in found_words for w in interesting_words]


def get_label_by_class(cl, classes):
    return classes.index(cl)

def get_classes_list(preprocessed_logs, min_occurences):
    first_word_frequencies = get_word_frequences(preprocessed_logs, lambda x: [x.get_first_word()])
    first_word_freq_stats = calc_frequency_stats(first_word_frequencies)
    classes = get_significant_words(first_word_freq_stats.keys(),
        lambda w, stats=first_word_freq_stats: stats[w]['__all_abs__'] > min_occurences)
    print("Classes: " + str(classes))
    return classes


def get_interesting_words_from_context(preprocessed_logs):
    word_frequencies = get_word_frequences(preprocessed_logs, lambda x: x.context_words)
    word_freq_stats = calc_frequency_stats(word_frequencies)
    interesting_context_words = get_significant_words(word_freq_stats.keys(), lambda w, stats=word_freq_stats: stats[w]['__all__'] > 0.0005)
    print("Context words: " + str(interesting_context_words))
    return interesting_context_words



def test_nn(logs_for_testing, classes, verbose=False):
    ranks = []
    top_3_count= 0
    top_5_count= 0
    for log in logs_for_testing:
        words = get_interesting_words_from_logs(log, interesting_words_from_context)
        vector = build_vector(words, interesting_words_from_context)
        result = net.activate(vector)
        sorted_result = sorted(enumerate(result),key=lambda x: x[1], reverse=True)
        class_label = get_label_by_class(log.first_word_cathegory, classes)
        rank_of_guess = list(map(lambda x: x[0], sorted_result)).index(class_label)
        if rank_of_guess <= 2:
            top_3_count += 1
        if rank_of_guess <= 4:
            top_5_count += 1
        if verbose:
            print(words)
            print("Chosen " + str(sorted_result[0][0]) + " " + str(classes[sorted_result[0][0]]) + " with probability " + str(sorted_result[0][1]))
            print("Chosen " + str(sorted_result[1][0]) + " " + str(classes[sorted_result[1][0]]) + " with probability " + str(sorted_result[1][1]))
            # print("Chosen " + str(sorted_result[2][0]) + " " + str(classes[sorted_result[2][0]]) + " with probability " + str(sorted_result[2][1]))
            print("Rank of guess: " + str(rank_of_guess))

            print(", but was: " + log.first_word_cathegory)
        ranks.append(rank_of_guess)
    return sum(ranks) / len(ranks), top_3_count / len(ranks), top_5_count / len(ranks)



def select_logs_for_training_and_testing(preprocessed_logs, classes, min_word_occurencies):
    shuffle(preprocessed_logs)
    logs_for_nn = []
    d = dict([(cl, 0) for cl in classes])
    for log in preprocessed_logs:
        if log.first_word_cathegory in classes and d[log.first_word_cathegory] < min_word_occurencies:
            logs_for_nn.append(log)
            d[log.first_word_cathegory] += 1
    print("N classes: " + str(len(classes)))
    print("Logs from each class: " + str(min_word_occurencies))
    print("Logs in total: " + str(len(logs_for_nn)))
    shuffle(logs_for_nn)
    div_point = int(len(logs_for_nn) * 0.25)
    return logs_for_nn[div_point:], logs_for_nn[:div_point]


def createDataSet(interesting_words_from_context, classes, n_hidden_layers, logs):
    n_input_nodes = len(interesting_words_from_context)
    n_output_nodes = len(classes)
    dataset = ClassificationDataSet(n_input_nodes, n_hidden_layers, nb_classes=n_output_nodes)
    for log in logs:
        words = get_interesting_words_from_logs(log, interesting_words_from_context)
        vector = build_vector(words, interesting_words_from_context)

        expected_class_label = get_label_by_class(log.first_word_cathegory, classes)
        dataset.addSample(vector, [expected_class_label])
    dataset._convertToOneOfMany()
    return dataset



if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--input-preprocessed-log-file', action='store', default='pplogs.pkl')
    parser.add_argument('--min-word-occurencies', action='store', type=int, default=2000)
    args = parser.parse_args()

    print("Starting deserializing extracted logs...")
    with open(args.input_preprocessed_log_file, 'rb') as i:
        preprocessed_logs = pickle.load(i)
    print("Done deserealizing extracted logs")
    # preprocessed_logs = preprocessed_logs[:2000]
    # classes = get_classes_list(preprocessed_logs, args.min_word_occurencies)
    classes = ['caught', 'creating']
    interesting_words_from_context = get_interesting_words_from_context(preprocessed_logs)

    preprocessed_logs = classify_logs_by_first_word(preprocessed_logs, classes)
    logs_for_training, logs_for_testing = select_logs_for_training_and_testing(preprocessed_logs, classes, args.min_word_occurencies)

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
# table of freqs of words in context depending on freqs THRESHOLD
# table of classes depending on threshold of OTHER (presenc in proj or just freq)
# consider ++ == = alone with tokens
# same amount of test data for different classes

