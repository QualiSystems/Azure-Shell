from azure.mgmt.network.models import IPAllocationMethod


def is_cloudshell_allocation(private_ip_allocation_method):
    try:
        return private_ip_allocation_method.lower() == 'cloudshell allocation'
    except AttributeError:
        return private_ip_allocation_method == IPAllocationMethod.static


def to_azure_type(private_ip_allocation_method):
    if private_ip_allocation_method.lower() == 'cloudshell allocation':
        return IPAllocationMethod.static
    return IPAllocationMethod.dynamic