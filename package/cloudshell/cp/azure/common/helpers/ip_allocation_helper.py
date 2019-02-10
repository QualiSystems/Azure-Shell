from azure.mgmt.network.models import IPAllocationMethod


# Azure Static Allocation is known as Cloudshell Allocation to users, can be set by attribute on cloud provider
def is_static_allocation(private_ip_allocation_method):
    try:
        return private_ip_allocation_method.lower() == IPAllocationMethod.static.name
    except AttributeError:
        return private_ip_allocation_method == IPAllocationMethod.static


def to_azure_type(private_ip_allocation_method):
    if private_ip_allocation_method.lower() == 'cloudshell allocation':
        return IPAllocationMethod.static
    return IPAllocationMethod.dynamic