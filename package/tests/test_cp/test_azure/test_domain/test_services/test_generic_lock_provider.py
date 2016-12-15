import threading
from unittest import TestCase

from mock import Mock

from cloudshell.cp.azure.domain.services.lock_service import GenericLockProvider


class TestGenericLockProvider(TestCase):
    def setUp(self):
        self.generic_lock_provider = GenericLockProvider()

    def test_lock_created_for_each_key(self):
        locks = []
        thread1 = LockCreatorThread(self.generic_lock_provider, locks)
        thread2 = LockCreatorThread(self.generic_lock_provider, locks)
        thread1.start()
        thread2.start()
        while len(locks) < 12:
            threading._sleep(0.001)
        self.assertEquals(len(locks), 12)
        self.assertEquals(len(list(set(locks))), 6)

    def test_lock_remove_for_each_key(self):
        locks = []

        for i in range(0, 6):
            locks.append(self.generic_lock_provider.get_resource_lock("key" + str(i), Mock()))

        self.generic_lock_provider.remove_lock_resource("key1", Mock())
        locks.append(self.generic_lock_provider.get_resource_lock("key1", Mock()))

        self.assertEquals(len(list(set(locks))), 7)


class LockCreatorThread(threading.Thread):
    def __init__(self, generic_lock_provider, locks):
        super(LockCreatorThread, self).__init__()
        self.locks = locks
        self.generic_lock_provider = generic_lock_provider

    def run(self):
        for i in range(0, 6):
            self.locks.append(self.generic_lock_provider.get_resource_lock("key" + str(i), Mock()))
