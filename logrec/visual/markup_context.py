import os

from logrec.util import io_utils

PATH_TO_CURRENT_DIR = os.path.dirname(os.path.realpath(__file__))
MARKED_UP_CONTEXTS_FILE=PATH_TO_CURRENT_DIR + '/../marked_up_contexts.txt'

def markup_contexts(logs, important_context_words):
    marked_up_contexts = []
    for log, words in zip(logs, important_context_words):
        marked_up_contexts.append(log.get_marked_up_context(words))
    return marked_up_contexts

if __name__ == '__main__':

    context_vectors = io_utils.load_context_vectors()
    logs_from_major_classes = io_utils.load_major_classes_logs()
    how_many = 5000
    marked_contexts = markup_contexts(logs_from_major_classes[:how_many],
                                      [log['values'] for log in context_vectors[:how_many]])
    with open(MARKED_UP_CONTEXTS_FILE, "w") as f:
        for m, log in zip(marked_contexts, logs_from_major_classes[:how_many]):
            f.write("[literal,subs=\"quotes\"]\n")
            f.write("*" + log.text + " + [" + log.id + "] *")
            f.write("\n\n")
            f.write(m)
            f.write("\n\n")