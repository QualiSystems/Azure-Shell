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

    def get_tags(self, vm_name, admin_username,subnet_name,reservation):
        """

        :param vm_name:
        :param admin_username:
        :param subnet_name:
        :type reservation: cloudshell.cp.azure.models.reservation_model.ReservationModel
        :return:
        """
        return {
                TagNames.Name: vm_name,
                TagNames.CreatedBy: TagService.CREATED_BY_QUALI,
                TagNames.Owner: reservation.owner,
                TagNames.ReservationId: reservation.reservation_id,
                TagNames.Blueprint: reservation.blueprint,
                TagNames.Domain: reservation.domain
                }


