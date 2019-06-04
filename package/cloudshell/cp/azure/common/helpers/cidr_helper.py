import netaddr


def is_cidr_format(cidr):
    """Validate that CIDR have a correct format. Example "10.10.10.10/24"

    :param str cidr:
    :param logging.Logger logger:
    :return: True/False whether CIDR is valid or not
    :rtype: bool
    """
    try:
        netaddr.IPNetwork(cidr)
    except netaddr.AddrFormatError:
        return False
    if '/' not in cidr:
        return False

    return True