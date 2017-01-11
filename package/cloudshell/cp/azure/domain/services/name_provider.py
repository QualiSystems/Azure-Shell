import uuid
import re


class NameProviderService(object):
    def generate_name(self, name, length=24):
        """Generate name based on the given one with a fixed length.

        Will replace all special characters (some Azure resources have this requirements).
        :param name: (str) App name
        :param length: (int) length for the generated name
        :return: (str) generated name
        """
        name = re.sub("[^a-zA-Z0-9]", "", name)
        generated_name = "{:.8}{}".format(name, uuid.uuid4().hex)

        return generated_name[:length]
