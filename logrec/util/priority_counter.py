import itertools
from heapq import heappush, heappop, heapify


class PriorityCounter(object):
    REMOVED = '<removed-task>'  # placeholder for a removed task

    def __init__(self, d):
        self.counter = itertools.count()
        self.pq = [[-value, next(self.counter), key] for key, value in d.items()]  # list of entries arranged in a heap
        heapify(self.pq)
        self.entry_finder = {entry[2]: entry for entry in self.pq}  # mapping of tasks to entries

    def add(self, pair, to_add):
        'Add a new task or update the priority of an existing task'
        count = next(self.counter)
        to_add = -to_add
        if pair in self.entry_finder:
            entry = self.entry_finder[pair]
            to_add = entry[0] + to_add
            self.remove_task(pair)
        if to_add != 0:
            entry = [to_add, count, pair]
            self.entry_finder[pair] = entry
            heappush(self.pq, entry)

    def remove_task(self, task):
        'Mark an existing task as REMOVED.  Raise KeyError if not found.'
        entry = self.entry_finder.pop(task)
        entry[-1] = PriorityCounter.REMOVED

    def pop_pair(self):
        'Remove and return the lowest priority task. Raise KeyError if empty.'
        while self.pq:
            priority, count, pair = heappop(self.pq)
            if pair is not PriorityCounter.REMOVED:
                del self.entry_finder[pair]
                return pair, -priority
        raise KeyError('pop from an empty priority queue')
