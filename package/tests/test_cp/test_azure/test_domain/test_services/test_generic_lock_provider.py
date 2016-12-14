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
            pass
        self.assertEquals(len(locks), 12)
        self.assertEquals(len(list(set(locks))), 6)


class LockCreatorThread(threading.Thread):
    def __init__(self, generic_lock_provider, locks):
        super(LockCreatorThread, self).__init__()
        self.locks = locks
        self.generic_lock_provider = generic_lock_provider

    def run(self):
        for i in range(0, 6):
            self.locks.append(self.generic_lock_provider.get_resource_lock("key" + str(i), Mock()))
