import uuid


class OperationsHelper:

    def __init__(self):
        pass

    @staticmethod
    def generate_name(name):
        return name.replace(" ", "") + ((str(uuid.uuid4())).replace("-", ""))[0:8]