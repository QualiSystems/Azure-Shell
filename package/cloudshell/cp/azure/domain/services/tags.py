class TagNames(object):
    CreatedBy = 'CreatedBy'
    Owner = 'Owner'
    Blueprint = 'Blueprint'
    ReservationId = 'ReservationId'
    Domain = 'Domain'
    Name = 'Name'
    Isolation = 'Isolation'


class TagService(object):
    CREATED_BY_QUALI = "Cloudshell"

    def __init__(self):
        pass

    def get_tags(self, vm_name, admin_username,subnet_name,reservation_id):
        """

        :return:
        """
        return {"test": "Igor",
                TagNames.Name: vm_name,
                TagNames.CreatedBy: TagService.CREATED_BY_QUALI,
                TagNames.Owner: admin_username,
                TagNames.Isolation: subnet_name,
                TagNames.ReservationId: reservation_id
                }


