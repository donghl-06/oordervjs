from urllib.parse import unquote

def params(request_entity, *param_list):
    return_param = {}
    if request_entity.method in ["GET"]:
        for param in param_list:
            param_value = request_entity.args.get(param)
            return_param[param] = unquote(param_value) if param_value is not None else param_value
    if request_entity.method in ["POST", "PATCH", "DELETE", "PUT"]:
        for param in param_list:
            return_param[param] = request_entity.form.get(param)
    return return_param