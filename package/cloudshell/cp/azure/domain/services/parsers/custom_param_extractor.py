class VmCustomParamsExtractor(object):

    def get_custom_param_value(self, custom_params, name):
        """Returns the value of the requested custom param

        :param custom_params: list[DeployDataHolder] array of VMCustomParams from the deployed app json
        :param name: (str) the name of the custom param to extract
        :return: the value of the custom param or None if custom param not found
        """
        name = name.lower()
        params = filter(lambda x: x.name.lower() == name, custom_params)

        if len(params) == 1:
            return params[0].value

        return None
