import uuid
import re


class NameProviderService(object):
    def generate_name(self, name, postfix=None, max_length=24):
        """Generate name based on the given one with a maximum allowed length.
        Will replace all special characters (some Azure resources have this requirements).
        :param str name: App name
        :param str postfix: If postfix is empty method will generate unique 8 char long id
        :param int max_length: Maximum allowed length for the generated name
        :return: (str) generated name
        :rtype: str
        """

        # replace special characters. Remove dash character only if at the beginning.
        name = re.sub("[^a-zA-Z0-9-]|^-+", "", name)

        if not postfix:
            postfix_len = 9  # length of the unique short string is 8 + 1 char for the dash separator
            postfix = self.generate_short_unique_string()
        else:
            postfix_len = len(postfix) + 1

        max_name_length = max_length - postfix_len
        truncated_name = name
        if len(name) > max_name_length:
            delta = len(name) - max_name_length
            truncated_name = name[:-delta]
        if truncated_name.endswith("-"):
            truncated_name = truncated_name[:-1]

        generated_name = "{0}-{1}".format(truncated_name, postfix)

        return generated_name

    def normalize_name(self, name):
        """
        Normalize a string to a valid azure resource name by replacing all whitespaces with dashes and lowering the case
        :param str name:
        :rtype: str
        """
        # normalize the app name to a valid Azure vm name
        if not name:
            return None
        return name.lower().replace(" ", "-")

    def generate_short_unique_string(self):
        """
        generate a short unique string.
        method generate a guid and return the first 8 characteres of the new guid
        :rtype: str
        """
        unique_id = str(uuid.uuid4())[:8]
        return unique_id

    def format_subnet_name(self, resource_group_name, subnet_cidr):
        return (resource_group_name + '_' + subnet_cidr).replace(' ', '').replace('/', '-')
