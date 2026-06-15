from functools import wraps


def sudo_support(fn):
    """Removes sudo before calling fn and adds it after."""
    @wraps(fn)
    def wrapper(command, *args, **kwargs):
        if not command.script.startswith('sudo '):
            return fn(command, *args, **kwargs)

        result = fn(command.update(script=command.script[5:]), *args, **kwargs)

        if result and isinstance(result, str):
            return u'sudo {}'.format(result)
        elif isinstance(result, list):
            return [u'sudo {}'.format(x) for x in result]
        else:
            return result
    return wrapper
