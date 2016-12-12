from threading import Lock


class GenericLockProvider(object):
    def __init__(self):
        self.lock_dictionary = {}

        self._lock = Lock()

    def _allocate_lock(self):
        """
        Allocates a new lock
        :return:
        """
        return Lock()

    def get_resource_lock(self, lock_key):
        """

        :param lock_dictionary: {}
        :param lock_key:uuid
        :return: Lock
        """
        # for performance
        if lock_key in self.lock_dictionary:
            return self.lock_dictionary[lock_key]

        with self._lock:
            if lock_key not in self.lock_dictionary:
                self.lock_dictionary[lock_key] = self._allocate_lock()
            return self.lock_dictionary[lock_key]

    def remove_lock_resource(self, lock_key):
        if lock_key in self.lock_dictionary:
            with self._lock:
                if lock_key in self.lock_dictionary:
                    del self.lock_dictionary[lock_key]
