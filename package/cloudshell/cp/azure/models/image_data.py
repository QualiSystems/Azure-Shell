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
