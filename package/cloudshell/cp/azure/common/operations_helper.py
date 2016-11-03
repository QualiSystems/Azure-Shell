import re
import uuid


class OperationsHelper:
    def __init__(self):
        pass

    @staticmethod
    def generate_name(name, length=24):
        """Generate name based on the given one with a fixed length.

        Will replace all special characters (some Azure resources have this requirements).
        :param name:
        :param length:
        :return:
        """
        name = re.sub("[^a-zA-Z0-9]", "", name)
        generated_name = "{:.8}{}".format(uuid.uuid4().hex, name)

        return generated_name[:length]
