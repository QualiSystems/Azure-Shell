import threading


class AbstractComparableInstance(object):
    """Abstract class that must be used together with SingletonByArgsMeta class"""

    def check_params_equality(self, *args, **kwargs):
        """Check if instance have the same attributes as provided in args and kwarg. Method must accept the same

        attributes as a __init__ one
        :param args: same args as for __init__ method
        :param kwargs: same kwargs as for __init__ method
        :return: (bool) True or False
        """
        raise NotImplementedError("Class {} must implement method 'check_params_equality'".format(type(self)))


class SingletonByArgsMeta(type):
    """Metaclass that allows to create single instances per same arguments

    Class that uses this metaclass must be a subclass of AbstractComparableInstance class and implement
    "check_params_equality" method
    Example usage:
        >>> class Test(AbstractComparableInstance):
        >>>     __metaclass__ = SingletonByArgsMeta
        >>>
        >>>     def __init__(self, a, b):
        >>>         self.a = a
        >>>         self.b = b
        >>>
        >>>     def check_params_equality(self, a, b):
        >>>         return self.a == a and self.b == b
        >>>
        >>> Test("a1" , "b1") is Test("a1" , "b1")
        >>> True
        >>>
        >>> Test("a1" , "b1") is Test("a2" , "b2")
        >>> False
    """
    __instances_by_cls = {}
    lock = threading.Lock()

    def __call__(cls, *args, **kwargs):
        if not issubclass(cls, AbstractComparableInstance):
            raise NotImplementedError("Class {} must inherit 'AbstractComparableInstance' "
                                      "if used with SingletonByArgsMeta metaclass".format(cls))

        with SingletonByArgsMeta.lock:
            instance = cls.__instances_by_cls.get(cls)

            if not (instance and instance.check_params_equality(*args, **kwargs)):
                instance = super(SingletonByArgsMeta, cls).__call__(*args, **kwargs)
                cls.__instances_by_cls[cls] = instance

        return instance
