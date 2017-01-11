class TestHelper(object):
    @staticmethod
    def CheckMethodCalledXTimes(method, call_count=1):
        return method.called and method.call_count == call_count
