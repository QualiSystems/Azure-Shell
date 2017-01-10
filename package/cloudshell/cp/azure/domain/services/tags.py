class TagNames(object):
    CreatedBy = 'CreatedBy'
    Owner = 'Owner'
    Blueprint = 'Blueprint'
    SandboxId = 'SandboxId'
    Domain = 'Domain'
    Name = 'Name'
    Isolation = 'Isolation'


class TagService(object):
    CREATED_BY_QUALI = "Cloudshell"

    def __init__(self):
        pass

    def get_tags(self, vm_name=None, reservation=None):
        """
        :param vm_name:
        :type reservation: cloudshell.cp.azure.models.reservation_model.ReservationModel
        :return:
        :rtype: dict
        """

        result = {TagNames.CreatedBy: TagService.CREATED_BY_QUALI}

        if vm_name:
            result.update({TagNames.Name: vm_name})
        if reservation.owner:
            result.update({TagNames.Owner: reservation.owner})
        if reservation.reservation_id:
            result.update({TagNames.SandboxId: reservation.reservation_id})
        if reservation.blueprint:
            result.update({TagNames.Blueprint: reservation.blueprint})
        if reservation.domain:
            result.update({TagNames.Domain: reservation.domain})

        return result

    def try_find_tag(self, tags_list, tag_key):
        """
        Gets a list of tags and a key to find and returns the value or None if not found
        :param tags_list: list of tags
        :param str tag_key:
        :return: tag value. None if tag key not found
        :rtype str:
        """
        if tags_list is None or tags_list.keys() is None:
            return None
        return next((tags_list[key] for key in tags_list.keys() if key == tag_key), None)
