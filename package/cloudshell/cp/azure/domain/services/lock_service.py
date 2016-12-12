from threading import Lock


class LockService(object):
    def __init__(self):
        self.lock = Lock()

    def _allocate_lock(self):
        """
        Allocates a new lock
        :return:
        """
        return Lock()

    def create_or_update_lock(self, lock_dictionary, lock_key):
        """

        :param lock_dictionary: {}
        :param lock_key:uuid
        :return: Lock
        """
        with self.lock:
            if lock_key not in lock_dictionary:
                lock_dictionary[lock_key] = self._allocate_lock()
            return lock_dictionary[lock_key]
