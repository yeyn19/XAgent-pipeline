from enum import Enum, unique
from abc import abstractmethod
from typing import Any
from dataclasses import dataclass, field
from copy import deepcopy
import json

from XAgent.tools.n8n_tools.n8n_utils import n8nParamParseStatus

expression_schema = "str(\"=.*($json\..*)\.*\")"

@unique
class n8nParameterType(Enum):
    """所有n8n json中支持的type
    """
    STRING = "string"
    NUMBER = "number"
    BOOLEAN = "boolean"
    LIST = "list"
    JSON = "json"
    COLOR = "color"
    DATATIME = "dateTime"
    COLLECTION = "collection"
    FIXEDCOLLECTION = "fixedCollection"
    OPTIONS = "options"
    MULTIOPTIONS = "multiOptions"
    RESOURCELOCATOR = "resourceLocator"
    RESOURCEMAPPER = "resourceMapper"
    NOTICE = "notice"
    ERROR = "error" #不能有这个


def visit_parameter(param_json: dict):
    """使用 vistor 模式进行解析
    """
    param_type = param_json["type"]

    # if param_type == n8nParameterType.NOTICE.value:
    #     return n8nNotice.visit(param_json)
    if param_type == n8nParameterType.BOOLEAN.value:
        return n8nBoolean.visit(param_json)
    elif param_type == n8nParameterType.NUMBER.value:
        return n8nNumber.visit(param_json)
    elif param_type == n8nParameterType.STRING.value:
        return n8nString.visit(param_json)
    elif param_type == n8nParameterType.OPTIONS.value:
        return n8nOption.visit(param_json)
    elif param_type == n8nParameterType.COLLECTION.value:
        return n8nCollection.visit(param_json)
    elif param_type == n8nParameterType.FIXEDCOLLECTION.value:
        return n8nFixedCollection.visit(param_json)
    elif param_type == n8nParameterType.RESOURCELOCATOR.value:
        return n8nResourceLocator.visit(param_json)
    else:
        print(f"{param_json['name']}: {param_type} not parsed")
        # raise NotImplementedError


@dataclass
class n8nParameter():
    father: 'n8nParameter' = None
    param_type: n8nParameterType = n8nParameterType.ERROR 

    name: str = ""
    required: bool = False
    default: Any = None
    description: str = ""
    no_data_expression: bool = False
    display_string: str = ""
    multiple_values: bool = False

    use_expression: bool = False
    data_is_set: bool = False

    def __init__(self, param_json):
        if "type" in param_json.keys():
            self.param_type = n8nParameterType(param_json["type"])
        if "name" in param_json.keys():
            self.name = param_json["name"]
        if "default" in param_json.keys():
            self.default = param_json["default"]
        if "required" in param_json.keys():
            self.required = param_json["required"]
        if "displayName" in param_json.keys():
            self.description = param_json["displayName"]
        if "description" in param_json.keys():
            self.description +=  ". " + param_json["description"]
        if "placeholder" in param_json.keys():
            self.description +=  f"({param_json['placeholder']})"

        if "noDataExpression" in param_json.keys():
            self.no_data_expression = param_json["noDataExpression"]


        if "displayOptions" in param_json.keys():
            if "show" in param_json.keys():
                for instance in param_json["displayOptions"]["show"]:
                    if instance not in ["resource", "operation"]:
                        expression = f"{instance} in {param_json['displayOptions']['show'][instance]}"
                        if self.display_string != "":
                            self.display_string += " and "
                        self.display_string += expression

        if "typeOptions" in param_json.keys() and "multipleValues" in param_json["typeOptions"].keys():
            self.multiple_values = param_json["typeOptions"]["multipleValues"]

    def get_depth(self):
        if self.father == None:
            return 1
        return self.father.get_depth() + 1

    @classmethod
    @abstractmethod
    def visit(cls, param_json):
        pass
    
    @abstractmethod
    def to_description(self, prefix_ids, indent=2, max_depth=1):
        pass

    @abstractmethod
    def parse_value(self, value: any) -> (n8nParamParseStatus, str):
        return n8nParamParseStatus.ParamParseSuccess, f"{self.get_parameter_name()} not implemented"

    def get_parameter_name(self):
        """递归获取paramter_name
        """
        if self.father == None:
            return f"params[\"{self.name}\"]"

        prefix_names = self.father.get_parameter_name()

        if self.father.param_type == n8nParameterType.COLLECTION and self.father.multiple_values:
            prefix_names += "[0]"
            return prefix_names +f"[\"{self.name}\"]"
        elif self.father.param_type == n8nParameterType.FIXEDCOLLECTION and self.father.multiple_values:
            assert self.param_type == n8nParameterType.COLLECTION, f"{self.param_type.name}"
            names = f"{prefix_names}[\"{self.name}\"]"
            return names
        elif self.father.param_type == n8nParameterType.RESOURCELOCATOR:
            for key,value in self.father.meta.items():
                if value == self:
                    name = f"{prefix_names}[\"value\"](when \"mode\"=\"{key}\")"
                    return name
        else:
            return prefix_names +f"[\"{self.name}\"]"
    
    def refresh(self):
        self.data_is_set = False

    def to_json(self):
        """递归转化: python_parameters -> n8n_json        
        """
        return None

@dataclass
class n8nNotice(n8nParameter):
    notice: str = ""

    def __init__(self, param_json):
        super().__init__(param_json)

    @staticmethod
    def visit(param_json):
        node = n8nNotice(param_json)

        node.notice = param_json["displayName"]
        return node

    def to_description(self, prefix_ids, indent=2, max_depth=1):
        return []
        # return [" "*indent + f"Notice: {self.notice}"]
    
@dataclass
class n8nNumber(n8nParameter):
    fixed_value: float = 0.0
    var: str = ""
    def __init__(self, param_json):
        super().__init__(param_json)
        self.fixed_value = 0.0
        self.var = ""
    @classmethod
    def visit(cls, param_json):
        node = n8nNumber(param_json)
        return node

    @abstractmethod
    def parse_value(self, value: any) -> (n8nParamParseStatus, str):
        if type(value) in [int, bool]:
            self.use_expression = False
            self.fixed_value = value
            self.data_is_set = True
            return n8nParamParseStatus.ParamParseSuccess, f"{self.get_parameter_name()} parsed as fixed_value"
        elif type(value) == str:
            if value.startswith("\"") and value.endswith("\""):
                value = value[1:-1]
            if self.no_data_expression:
                return n8nParamParseStatus.UnsupportedExpression, f"{self.get_parameter_name()} don't support expression"
            # TODO: check expression available
            if not value.startswith("="):
                return n8nParamParseStatus.ExpressionError, f"{self.get_parameter_name()} doesn't have a expression schema: {expression_schema}"

            self.var = value
            self.use_expression = True
            self.data_is_set = True
            return n8nParamParseStatus.ParamParseSuccess, f"{self.get_parameter_name()} parsed as expression" 
        else:
            available_types = ["int", "float"]
            if not self.no_data_expression:
                available_types.append(expression_schema)
            return n8nParamParseStatus.ParamTypeError, f"{self.get_parameter_name()} can only be parsed as {available_types}, got {json.dumps(value)}" 

    def to_description(self, prefix_ids, indent=2, max_depth=1):
        all_name = self.get_parameter_name()
        line1 = " "*indent + f"{prefix_ids} {all_name}: {self.param_type.value}"

        if self.default != None:
            line1 += f" = {self.default}"
        if self.display_string != "":
            if self.required:
                line1 += f", Required when ({self.display_string}), otherwise do not provide"
            else:
                line1 += f", Activate(Not Required) when ({self.display_string}), otherwise do not provide"
        else:
            if self.required:
                line1 += f", Required"

        line1 +=  f": {self.description}"
        if self.no_data_expression:
            line1 += f". You can't use expression."
        return [line1]

    def to_json(self):
        """递归转化: python_parameters -> n8n_json        
        """
        if not self.data_is_set:
            return None
        if self.use_expression:
            return self.var
        else:
            return self.fixed_value


@dataclass
class n8nBoolean(n8nParameter):
    fixed_value: bool = False
    var: str = ""

    def __init__(self, param_json):
        super().__init__(param_json)
        self.fixed_value = False
        self.var = ""
    @classmethod
    def visit(cls, param_json):
        node = n8nBoolean(param_json)

        return node

    @abstractmethod
    def parse_value(self, value: any) -> (n8nParamParseStatus, str):
        if type(value) == bool:
            self.use_expression = False
            self.fixed_value = value
            self.data_is_set = True
            return n8nParamParseStatus.ParamParseSuccess, f"{self.get_parameter_name()} parsed as fixed_value"
        elif type(value) == str:
            if value.startswith("\"") and value.endswith("\""):
                value = value[1:-1]
            if self.no_data_expression:
                return n8nParamParseStatus.UnsupportedExpression, f"{self.get_parameter_name()} don't support expression"
            # TODO: check expression available
            if not value.startswith("="):
                return n8nParamParseStatus.ExpressionError, f"{self.get_parameter_name()} doesn't have a expression schema: {expression_schema}"

            self.var = value
            self.use_expression = True
            self.data_is_set = True
            return n8nParamParseStatus.ParamParseSuccess, f"{self.get_parameter_name()} parsed as expression" 
        else:
            available_types = ["bool"]
            if not self.no_data_expression:
                available_types.append(expression_schema)
            return n8nParamParseStatus.ParamTypeError, f"{self.get_parameter_name()} can only be parsed as {available_types}, got {json.dumps(value)}" 


    def to_description(self, prefix_ids, indent=2, max_depth=1):
        all_name = self.get_parameter_name()
        line1 = " "*indent + f"{prefix_ids} {all_name}: {self.param_type.value}"

        if self.default != None:
            line1 += f" = {self.default}"
        if self.display_string != "":
            if self.required:
                line1 += f", Required when ({self.display_string}), otherwise do not provide"
            else:
                line1 += f", Activate(Not Required) when ({self.display_string}), otherwise do not provide"
        else:
            if self.required:
                line1 += f", Required"

        line1 +=  f": {self.description}"
        if self.no_data_expression:
            line1 += f". You can't use expression."
        return [line1]
    
    def to_json(self):
        """递归转化: python_parameters -> n8n_json        
        """
        if not self.data_is_set:
            return None
        if self.use_expression:
            return self.var
        else:
            return self.fixed_value

@dataclass
class n8nString(n8nParameter):
    value: str = ""
    def __init__(self, param_json):
        super().__init__(param_json)
        self.value = ""
    @classmethod
    def visit(cls, param_json):
        node = n8nString(param_json)
        #TODO: validation
        return node

    @abstractmethod
    def parse_value(self, value: any) -> (n8nParamParseStatus, str):
        if type(value) == str:
            if value.startswith("\"") and value.endswith("\""):
                value = value[1:-1]

            if value.startswith("="):
                if self.no_data_expression:
                    return n8nParamParseStatus.UnsupportedExpression, f"{self.get_parameter_name()} don't support expression"
                # TODO: check expression available
                self.value = value
                self.data_is_set = True
                return n8nParamParseStatus.ParamParseSuccess, f"{self.get_parameter_name()} parsed as expression" 
            else:
                self.value = value
                self.data_is_set = True
                return n8nParamParseStatus.ParamParseSuccess, f"{self.get_parameter_name()} parsed as normal-string" 
        else:
            available_types = ["str"]
            if not self.no_data_expression:
                available_types.append(expression_schema)
            return n8nParamParseStatus.ParamTypeError, f"{self.get_parameter_name()} can only be parsed as {available_types}, got {json.dumps(value)}" 

    def to_description(self, prefix_ids, indent=2, max_depth=1):
        all_name = self.get_parameter_name()
        line1 = " "*indent + f"{prefix_ids} {all_name}: {self.param_type.value}"

        if self.default != None:
            line1 += f" = \"{self.default}\""
        if self.display_string != "":
            if self.required:
                line1 += f", Required when ({self.display_string}), otherwise do not provide"
            else:
                line1 += f", Activate(Not Required) when ({self.display_string}), otherwise do not provide"
        else:
            if self.required:
                line1 += f", Required"

        line1 +=  f": {self.description}"
        if self.no_data_expression:
            line1 += f". You can't use expression."
        return [line1]
    
    def to_json(self):
        if not self.data_is_set:
            return None
        return self.value

@dataclass
class n8nOption(n8nParameter):
    value: str = ""

    enum: list = field(default_factory=list)
    enum_descriptions: list = field(default_factory=list)

    def __init__(self, param_json):
        super().__init__(param_json)
        self.enum = []
        self.enum_descriptions = []

    @classmethod
    def visit(cls, param_json):
        node = n8nOption(param_json)
        # print(param_json)
        if "options" in param_json.keys():
            for cont in param_json["options"]:
                node.enum.append(cont["value"])
                enum_des = cont["name"]
                if "description" in cont.keys():
                    enum_des += f". {cont['description']}"
                node.enum_descriptions.append(enum_des)
        else:
            #TODO loadOptionsMethod

            pass
        return node

    @abstractmethod
    def parse_value(self, value: any) -> (n8nParamParseStatus, str):
        if type(value) == str:
            if value.startswith("\"") and value.endswith("\""):
                value = value[1:-1]
            if "," in value:
                return n8nParamParseStatus.ParamTypeError, f"{self.get_parameter_name()} doesn't support multiple values (split by ',')"

            if value.startswith("="):
                if self.no_data_expression:
                    return n8nParamParseStatus.UnsupportedExpression, f"{self.get_parameter_name()} don't support expression"
                # TODO: check expression available
                self.value = value
                self.data_is_set = True
                return n8nParamParseStatus.ParamParseSuccess, f"{self.get_parameter_name()} parsed as expression" 
            else:
                if value not in self.enum:
                    return n8nParamParseStatus.ParamTypeError, f"{self.get_parameter_name()} should in {self.enum}, found \"{value}\""
                self.value = value
                self.data_is_set = True
                return n8nParamParseStatus.ParamParseSuccess, f"{self.get_parameter_name()} parsed as normal-string" 
        else:
            available_type = f"enum[str] in {self.enum}"
            return n8nParamParseStatus.ParamTypeError, f"{self.get_parameter_name()} can only be parsed as {available_type}, got {json.dumps(value)}" 


    def to_description(self, prefix_ids, indent=2, max_depth=1):
        all_name = self.get_parameter_name()
        lines = []
        line1 = f"{prefix_ids} {all_name}: enum[string]"

        if self.default != None:
            line1 += f" = \"{self.default}\""
        if self.display_string != "":
            if self.required:
                line1 += f", Required when ({self.display_string}), otherwise do not provide"
            else:
                line1 += f", Activate(Not Required) when ({self.display_string}), otherwise do not provide"
        else:
            if self.required:
                line1 += f", Required"

        line1 +=  f": {self.description} "
        if self.no_data_expression:
            line1 += f" You can't use expression."
        line1 += f". Available values:"
        lines.append(line1)
        for k, (enum,des) in enumerate(zip(self.enum, self.enum_descriptions)):
            lines.append(f"  {prefix_ids}.{k} value==\"{enum}\": {des}")
        
        lines = [" "*indent + line for line in lines]
        return lines
    
    def to_json(self):
        if not self.data_is_set:
            return None
        return self.value

@dataclass
class n8nCollection(n8nParameter):
    meta: dict = field(default_factory=dict)
    value: dict = field(default_factory=list)

    def __init__(self, param_json):
        super().__init__(param_json)
        self.meta = {}
        self.value = []

    @classmethod
    def visit(cls, param_json):
        node = n8nCollection(param_json)
        # print(param_json)
        # exit()
        if type(node.default) == dict and node.multiple_values:
            node.default = [node.default]
        if "options" in param_json.keys():
            for instance in param_json["options"]:
                name = instance["name"]
                sub_param = visit_parameter(instance)
                if sub_param != None:
                    node.meta[name] = sub_param
                    node.meta[name].father = node
        else:
            #TODO loadOptionsMethod
            assert False
            
        return node

    def parse_single_dict(self, value, list_count=False) -> (n8nParamParseStatus, str, dict):
        assert type(value) == dict, f"{value}"

        new_value = {}
        for key in value.keys():
            if key not in self.meta.keys():
                if list_count != -1:
                    param_name = f"{self.get_parameter_name()}[{list_count}]"
                else:
                    param_name = self.get_parameter_name()
                return n8nParamParseStatus.UndefinedParam, f"Undefined property \"{key}\" for {param_name}, supported properties: {list(self.meta.keys())}", {}
            right_value_subparam = deepcopy(self.meta[key])
            sub_param_status, sub_param_parse_result = right_value_subparam.parse_value(value[key])
            if sub_param_status != n8nParamParseStatus.ParamParseSuccess:
                return sub_param_status, sub_param_parse_result, {}
            new_value[key] = right_value_subparam
        return n8nParamParseStatus.ParamParseSuccess, "", new_value

    @abstractmethod
    def parse_value(self, value: any) -> (n8nParamParseStatus, str):
        # print(value)
        if type(value) == list:
            if not self.multiple_values:
                return n8nParamParseStatus.ParamTypeError, f"{self.get_parameter_name()} can only be parsed as dict, got {json.dumps(value)}" 

            new_value = []
            for k, content in enumerate(value):
                status_code, result, output_result = self.parse_single_dict(content, list_count=k)
                if status_code != n8nParamParseStatus.ParamParseSuccess:
                    return status_code, result
                new_value.append(output_result)
            self.value = new_value
            self.data_is_set = True
            return n8nParamParseStatus.ParamParseSuccess, f"{self.get_parameter_name()} parsed as list with {len(self.value)} items"

        elif type(value) == dict:

            if self.multiple_values:
                return n8nParamParseStatus.ParamTypeError, f"{self.get_parameter_name()} can only be parsed as list[dict], got {json.dumps(value)}" 
            status_code, result, output_result = self.parse_single_dict(value, list_count = -1)
            if status_code != n8nParamParseStatus.ParamParseSuccess:
                return status_code, result
            self.value.append(output_result)
            self.data_is_set = True
            return n8nParamParseStatus.ParamParseSuccess, f"{self.get_parameter_name()} parsed as dict, got {json.dumps(value)}"

        elif type(value) == str:
            #TODO support expression
            return n8nParamParseStatus.ParamTypeError, f"{self.get_parameter_name()} doesn't support expression now" 
       
        else:
            if self.multiple_values:
                available_type = "list[dict]"
            else:
                available_type = "dict"
            return n8nParamParseStatus.ParamTypeError, f"{self.get_parameter_name()} can only be parsed as {available_type}, got {type(value)}" 


    def to_description(self, prefix_ids, indent=2, max_depth=1):
        all_name = self.get_parameter_name()
        lines = []
        if self.multiple_values:
            type_string = "list[dict]"
        else:
            type_string = "dict"
        line1 = f"{prefix_ids} {all_name}: {type_string}"

        if self.default != None:
            line1 += f" = {self.default}"
        if self.display_string != "":
            if self.required:
                line1 += f", Required when ({self.display_string}), otherwise do not provide"
            else:
                line1 += f", Activate(Not Required) when ({self.display_string}), otherwise do not provide"
        else:
            if self.required:
                line1 += f", Required"

        line1 +=  f": {self.description} "
        if self.no_data_expression:
            line1 += f" You can't use expression."
        line1 += f". properties description:"
        lines.append(" "*indent + line1)
        if self.get_depth() >= max_depth and self.required == False:
            lines.append(" "*indent+ "  ...hidden...")
        elif self.required:
            for k, (property_name, property) in enumerate(self.meta.items()):
                sublines = property.to_description(prefix_ids+f".{k}", indent=indent+2, max_depth=1000)
                lines.extend(sublines)
        else:
            for k, (property_name, property) in enumerate(self.meta.items()):
                sublines = property.to_description(prefix_ids+f".{k}", indent=indent+2, max_depth=max_depth)
                lines.extend(sublines)

        return lines
    
    def refresh(self):
        self.data_is_set = False
        self.value.clear()
        for key in self.meta.keys():
            self.meta[key].refresh()

    def to_json(self):
        if not self.data_is_set:
            return None
        
        if self.multiple_values:
            json_data = [{key: value.to_json() for key, value in data.items()} for data in self.value]
            return json_data
        else:
            json_data = {key: value.to_json() for key, value in self.value[0]}
        
        return json_data

    
@dataclass
class n8nFixedCollection(n8nParameter):
    """实现上是{}，里面的value是Collection
    """
    meta: dict = field(default_factory=dict)
    value: dict = field(default_factory=list)

    def __init__(self, param_json):
        super().__init__(param_json)
        self.meta = {}
        self.value = {}

    @classmethod
    def visit(cls, param_json):
        node = n8nFixedCollection(param_json)
        # print(param_json)
        # exit()

        if "options" in param_json.keys():
            for instance in param_json["options"]:
                name = instance["name"]

                sub_node = n8nCollection(instance)
                sub_node.param_type = n8nParameterType.COLLECTION
                sub_node.multiple_values = node.multiple_values


                if type(sub_node.default) == dict and sub_node.multiple_values:
                    sub_node.default = [sub_node.default]
                if "values" in instance.keys():
                    for sub_instance in instance["values"]:
                        subparam_key_name = sub_instance["name"]
                        sub_sub_param = visit_parameter(sub_instance)
                        if sub_sub_param != None:
                            sub_node.meta[subparam_key_name] = sub_sub_param
                            sub_node.meta[subparam_key_name].father = sub_node
                else:
                    #TODO loadOptionsMethod
                    assert False
                
                node.meta[name] = sub_node
                node.meta[name].father = node
        else:
            #TODO loadOptionsMethod
            assert False
            
        return node

    def to_json(self):
        if not self.data_is_set:
            return None
        json_data = {}
        for key,value in self.value.items():
            sub_param = value.to_json()
            if sub_param != None:
                json_data[key] = sub_param
    
        return json_data

    @abstractmethod
    def parse_value(self, value: any) -> (n8nParamParseStatus, str):
        if type(value) == dict:
            new_value = {}
            for key in value.keys():
                if key not in self.meta.keys():
                    return n8nParamParseStatus.UndefinedParam, f"Undefined property \"{key}\" for {self.get_parameter_name()}, supported properties: {list(self.meta.keys())}"
                new_param = deepcopy(self.meta[key])
                subparam_status, subparam_data = new_param.parse_value(value=value[key])
                if subparam_status != n8nParamParseStatus.ParamParseSuccess:
                    return subparam_status, subparam_data
                new_value[key] = new_param
            self.data_is_set = True
            self.value = new_value
            return n8nParamParseStatus.ParamParseSuccess, f"{self.get_parameter_name()} parsed with keys: {list(self.value.keys())}"
        else:
            if self.multiple_values:
                available_type = "dict[str,list[dict[str,any]]]"
            else:
                available_type = "dict[str,dict[str,any]]"
            return n8nParamParseStatus.ParamTypeError, f"{self.get_parameter_name()} can only be parsed as {available_type}, got {json.dumps(value)}" 


    def refresh(self):
        self.data_is_set = False
        self.value.clear()
        for key in self.meta.keys():
            self.meta[key].refresh()

    def to_description(self, prefix_ids, indent=2, max_depth=1):
        all_name = self.get_parameter_name()
        lines = []
        if self.multiple_values:
            type_string = "dict[str,list[dict[str,any]]]"
        else:
            type_string = "dict[str,dict[str,any]]"
        line1 = f"{prefix_ids} {all_name}: {type_string}"

        if self.default != None:
            line1 += f" = {self.default}"
        if self.display_string != "":
            if self.required:
                line1 += f", Required when ({self.display_string}), otherwise do not provide"
            else:
                line1 += f", Activate(Not Required) when ({self.display_string}), otherwise do not provide"
        else:
            if self.required:
                line1 += f", Required"

        line1 +=  f": {self.description} "
        if self.no_data_expression:
            line1 += f" You can't use expression."
        line1 += f". properties description:"
        lines.append(" "*indent + line1)

        if self.get_depth() >= max_depth and self.required == False:
            lines.append(" "*indent+ "  ...hidden...")
        elif self.required:
            for k, (property_name, property) in enumerate(self.meta.items()):
                sublines = property.to_description(prefix_ids+f".{k}", indent=indent+2, max_depth=1000)
                lines.extend(sublines)
        else:
            for k, (property_name, property) in enumerate(self.meta.items()):
                sublines = property.to_description(prefix_ids+f".{k}", indent=indent+2, max_depth=max_depth)
                lines.extend(sublines)

        # for k, (property_name, property) in enumerate(self.meta.items()):
        #     sublines = property.to_description(prefix_ids+f".{k}", indent=indent+2)
        #     lines.extend(sublines)

        return lines


    
@dataclass
class n8nResourceLocator(n8nParameter):
    meta: dict = field(default_factory=dict)
    mode: str = ""
    value: any = None

    def __init__(self, param_json):
        super().__init__(param_json)
        self.meta = {}
        self.mode = ""
        self.value = None

    @classmethod
    def visit(cls, param_json):
        node = n8nResourceLocator(param_json)
        assert "modes" in param_json.keys()
        for instance in param_json["modes"]:
            name = instance["name"]
            result_node = visit_parameter(instance)
            if result_node != None:
                node.meta[name] = result_node
                node.meta[name].father = node
    
        return node

    def refresh(self):
        self.data_is_set = False

    def to_description(self, prefix_ids, indent=2, max_depth=1):
        all_name = self.get_parameter_name()
        lines = []
        type_string = "dict{\"mode\":enum(str),\"values\":any}"
        line1 = f"{prefix_ids} {all_name}: {type_string}"

        if self.default != None:
            line1 += f" = {self.default}"
        if self.display_string != "":
            if self.required:
                line1 += f", Required when ({self.display_string}), otherwise do not provide"
            else:
                line1 += f", Activate(Not Required) when ({self.display_string}), otherwise do not provide"
        else:
            if self.required:
                line1 += f", Required"
    
        line1 +=  f": {self.description} "
        if self.no_data_expression:
            line1 += f" You can't use expression."
        line1 += f". \"mode\" should be one of {list(self.meta.keys())}: "
        lines.append(" "*indent + line1)


        if self.get_depth() >= max_depth and self.required == False:
            lines.append(" "*indent+ "  ...hidden...")
        elif self.required:
            for k, key in enumerate(self.meta.keys()):
                new_lines = self.meta[key].to_description(f"{prefix_ids}.{k}", indent=indent+2, max_depth=1000)
                lines.extend(new_lines)
        else:
            for k, key in enumerate(self.meta.keys()):
                new_lines = self.meta[key].to_description(f"{prefix_ids}.{k}", indent=indent+2, max_depth=max_depth)
                lines.extend(new_lines)

        return lines

    def to_json(self):
        if not self.data_is_set:
            return None
        json_data = {
            "mode": self.mode,
            "value": self.value.to_json()
        }
        return json_data

    @abstractmethod
    def parse_value(self, value: any) -> (n8nParamParseStatus, str):
        if type(value) == dict and (list(value.keys()) == ["mode","value"] or list(value.keys()) == ["value","mode"]):
            if value["mode"] not in self.meta.keys():
                return n8nParamParseStatus.UndefinedParam, f"Undefined mode \"{value['mode']}\" for {self.get_parameter_name()}, supported modes: {list(self.meta.keys())}"
            value_value = value["value"]
            temp_value = deepcopy(self.meta[value["mode"]])
            subparam_status, subparam_data = temp_value.parse_value(value=value_value)
            if subparam_status != n8nParamParseStatus.ParamParseSuccess:
                return subparam_status, subparam_data
            self.data_is_set = True
            self.mode = value["mode"]
            self.value = temp_value
            return n8nParamParseStatus.ParamParseSuccess, f"{self.get_parameter_name()} parsed with \"mode\"={self.mode}"
        else:
            available_type = "dict{\"mode\":str, \"value\":any}"
            return n8nParamParseStatus.ParamTypeError, f"{self.get_parameter_name()} can only be parsed as {available_type}, got {json.dumps(value)}"