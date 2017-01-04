class ImageDataModel(object):
    def __init__(self, os_type, purchase_plan):
        """
        :param azure.mgmt.compute.models.OperatingSystemTypes os_type:
        :param azure.mgmt.compute.models.PurchasePlan purchase_plan:
        :return:
        """
        self.purchase_plan = purchase_plan
        self.os_type = os_type
