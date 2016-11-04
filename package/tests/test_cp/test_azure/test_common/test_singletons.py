from unittest import TestCase

from cloudshell.cp.azure.common.singletons import AbstractComparableInstance
from cloudshell.cp.azure.common.singletons import SingletonByArgsMeta


class TestSingletonByArgsMeta(TestCase):
    def test_metaclass_will_return_same_instance(self):
        """Check that metaclass call will return same instance for the same arguments"""
        class TestedClass(AbstractComparableInstance):
            __metaclass__ = SingletonByArgsMeta

            def __init__(self, a, b, c):
                self.a = a
                self.b = b
                self.c = c

            def check_params_equality(self, a, b, c):
                return self.a == a and self.b == b

        # Verify
        # for the same "a" and "b" attributes it will be the same instance
        self.assertIs(TestedClass(1, 2, 10), TestedClass(1, 2, 50))
        # for the different "a" and "b" attributes instances wouldn't be the same
        self.assertIsNot(TestedClass(1, 2, 30), TestedClass(2, 3, 30))

    def test_metaclass_raises_exception_if_class_does_not_inherit_comparable_interface(self):
        """Check that metaclass call will raise an exception if class hasn't implement AbstractComparableInstance"""
        class TestedClass(object):
            __metaclass__ = SingletonByArgsMeta

            def __init__(self, a, b, c):
                self.a = a
                self.b = b
                self.c = c

            def check_params_equality(self, a, b, c):
                return self.a == a and self.b == b

        # Verify
        with self.assertRaises(NotImplementedError):
            TestedClass(1, 10, 20)


class TestAbstractComparableInstance(TestCase):
    def test_check_params_equality_raises_exception_if_it_was_not_implemented(self):
        """Check that method will raise an exception if it wasn't implemented in a child class"""
        class TestedClass(AbstractComparableInstance):
            pass

        tested_instance = TestedClass()

        # Verify
        with self.assertRaises(NotImplementedError):
            tested_instance.check_params_equality()
