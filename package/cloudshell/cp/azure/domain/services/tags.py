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

    def get_tags(self, vm_name, admin_username, subnet_name, reservation):
        """

        :param vm_name:
        :param admin_username:
        :param subnet_name:
        :type reservation: cloudshell.cp.azure.models.reservation_model.ReservationModel
        :return:
        """

        result = {TagNames.CreatedBy: TagService.CREATED_BY_QUALI}

        if vm_name:
            result.update({TagNames.Name: vm_name})
        if reservation:
            result.update({TagNames.Owner: reservation.owner})
        if reservation:
            result.update({TagNames.ReservationId: reservation.reservation_id})
        if reservation:
            result.update({TagNames.Blueprint: reservation.blueprint})
        if reservation:
            result.update({TagNames.Domain: reservation.domain})

        return result
