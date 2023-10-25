import uuid,base64,os
from colorama import Fore
from XAgent.logs import logger

def is_wrapped_response(obj:dict) -> bool:
    if 'type' in obj and obj['type'] in ['simple','composite','binary'] and 'data' in obj:
        return True
    return False
def unwrap_tool_response(obj):
    if isinstance(obj,dict):
        if is_wrapped_response(obj):
            match obj['type']:
                case 'simple':
                    return obj['data']
                case 'binary':
                    name = obj.get('name',uuid.uuid4().hex)
                    if obj['media_type'] == 'image/png' and not str(name).endswith('.png'):
                        name += '.png'
                    with open(os.path.join('local_workspace',name),'wb') as f:
                        f.write(base64.b64decode(obj['data']))
                    return {
                        'media_type': obj['media_type'],
                        'file_name': name
                        }
                case 'composite':
                    return [unwrap_tool_response(o) for o in obj['data']]
        else:
            return obj
    elif isinstance(obj,(str,int,float,bool,list)):
        return obj
    elif obj is None:
        return None
    else:
        logger.typewriter_log(f'Unknown type {type(obj)} in unwrap_tool_response',Fore.YELLOW)
        return None
