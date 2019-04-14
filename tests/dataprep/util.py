import unittest
from multiprocessing import Process

from logrec.dataprep.util import merge_dicts_, AtomicInteger


class UtilTest(unittest.TestCase):
    def test_merge_dicts(self):
        dict1 = {"a": 3, "b": 4}
        dict2 = {"b": 5, "c": 6}

        merge_dicts_(dict1, dict2)

        expected = {"a": 3, "b": 9, "c": 6}

        self.assertEqual(expected, dict1)

    def test_atomic_integer_thread_safety1(self):
        def inc(atomic_integer: AtomicInteger) -> None:
            for i in range(100):
                atomic_integer.inc()

        ai = AtomicInteger()
        thread1 = Process(target=inc, args=(ai,))
        thread2 = Process(target=inc, args=(ai,))
        thread3 = Process(target=inc, args=(ai,))

        thread1.start()
        thread2.start()
        thread3.start()

        thread1.join()
        thread2.join()
        thread3.join()

        self.assertEqual(300, ai.value)


if __name__ == '__main__':
    unittest.main()
