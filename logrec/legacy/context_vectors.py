import argparse

from logrec.util import io

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--context-lines-to-consider', action='store', type=int, default=4)
    args = parser.parse_args()

    logs_from_major_classes = io.load_major_classes_logs()
    interesting_words_from_context = io.load_interesting_words()

    binary_context_vectors = [{'id': log.id,
                               'values': [w in log.get_context_words(args.context_lines_to_consider)
                                    for w in interesting_words_from_context]} for log in logs_from_major_classes]

    context_vectors = [{'id': l.id, 'values': [w for w in l.get_context_words(args.context_lines_to_consider)
                if w in interesting_words_from_context]} for l in logs_from_major_classes]

    io.dump_binary_context_vectors(binary_context_vectors)
    io.dump_context_vectors(context_vectors)
