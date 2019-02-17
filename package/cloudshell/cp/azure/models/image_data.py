class ImageDataModelBase(object):
    def __init__(self, os_type):
        """
        :param azure.mgmt.compute.models.OperatingSystemTypes os_type:
        :return:
        """
        self.os_type = os_type


class MarketplaceImageDataModel(ImageDataModelBase):
    def __init__(self, os_type, purchase_plan):
        """
        :param azure.mgmt.compute.models.OperatingSystemTypes os_type:
        :param azure.mgmt.compute.models.PurchasePlan purchase_plan:
        :return:
        """
        super(MarketplaceImageDataModel, self).__init__(os_type)
        self.purchase_plan = purchase_plan


class CustomImageDataModel(ImageDataModelBase):
    def __init__(self, image_id, os_type):
        """
        :param str image_id:
        :param azure.mgmt.compute.models.OperatingSystemTypes os_type:
        :return:
        """
        super(CustomImageDataModel, self).__init__(os_type)
        self.image_id = image_id


class SnapshotDataModel(ImageDataModelBase):
    def __init__(self, snapshot_id, os_type, snapshot_name, snapshot_resource_group):
        """
        :param str snapshot_id:
        :param azure.mgmt.compute.models.OperatingSystemTypes os_type:
        :param str snapshot_name:
        :param str snapshot_resource_group:
        :return:
        """
        super(SnapshotDataModel, self).__init__(os_type)
        self.snapshot_id = snapshot_id
        self.snapshot_name = snapshot_name,
        self.snapshot_resource_group = snapshot_resource_group
