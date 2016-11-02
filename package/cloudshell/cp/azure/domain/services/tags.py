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

    def get_tags(self, vm_name=None, admin_username=None, subnet_name=None, reservation=None):
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
        if reservation.owner:
            result.update({TagNames.Owner: reservation.owner})
        if reservation.reservation_id:
            result.update({TagNames.ReservationId: reservation.reservation_id})
        if reservation.blueprint:
            result.update({TagNames.Blueprint: reservation.blueprint})
        if reservation.domain:
            result.update({TagNames.Domain: reservation.domain})

        return result


    def try_find_tag(self,tags_list, tag_key):
        """
        Gets a list of tags and a key to find and returns the value or None if not found

        :param tags_list {}: list of tags
        :param tag_key:
        :return:
        """
        return next((tags_list[key] for key in tags_list.keys() if key == tag_key), None)

