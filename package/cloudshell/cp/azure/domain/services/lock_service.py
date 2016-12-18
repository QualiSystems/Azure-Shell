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

    def get_resource_lock(self, lock_key, logger):
        """
        :param logging.Logger logger: logger instance
        :param str lock_key:
        :return: Lock
        """
        if lock_key not in self.lock_dictionary:
            with self._lock:
                if lock_key not in self.lock_dictionary:
                    logger.info("Creating lock object for {}".format(lock_key))
                    self.lock_dictionary[lock_key] = self._allocate_lock()
        return self.lock_dictionary[lock_key]

    def remove_lock_resource(self, lock_key, logger):
        if lock_key in self.lock_dictionary:
            with self._lock:
                if lock_key in self.lock_dictionary:
                    logger.info("Removing lock object for {}".format(lock_key))
                    del self.lock_dictionary[lock_key]
