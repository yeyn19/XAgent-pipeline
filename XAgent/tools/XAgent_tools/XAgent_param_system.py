




class XAgentParamSystem(ParamSystem):
    

    def from_json(self):
        pass

    def partly_implement(self, given_param_dict):
        pass

    

    def to_description(self):
        """向语言模型描述待填写参数
        """
        pass

    @abstractmethod
    def run(self, input_params: dict):
        pass