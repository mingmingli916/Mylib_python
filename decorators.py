import logging
import functools
import os
import tempfile
import inspect


def logged(file=None, level='debug'):
    """
    Log the output of the decorated function into a logged file.

    :param file: If file is None, use temple file, otherwise use the given file
    :param level: Log level. If level is None, do not log anything.
    :return: decorated function
    """
    levels = {'debug', 'info', 'warning', 'error', 'fatal'}

    def decorator(function):
        logger = logging.getLogger('Logger')
        if level in levels:
            logger.setLevel(getattr(logging, level.upper()))
        else:
            logger.setLevel(logging.INFO)
        logger.propagate = False

        if file is None:
            handler = logging.FileHandler(os.path.join(tempfile.gettempdir(), 'logged.log'))
        else:
            handler = logging.FileHandler(file)
        logger.handlers.clear()  # This is used to avoid duplicated output.
        logger.addHandler(handler)

        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            # accumulate string
            log = 'called: ' + function.__name__ + '('
            log += ', '.join([f'{a!r}' for a in args] + [f'{k!s}={v!r}' for k, v in kwargs.items()])
            result = exception = None
            try:
                result = function(*args, **kwargs)
                return result
            except Exception as err:
                exception = err
            finally:
                log += (') -> ' + str(result)) if exception is None else f'{type(exception)}: {exception}'
                getattr(logger, level.lower())(log)

                if exception is not None:
                    raise exception

        return wrapper

    return decorator


def bounded(minimum, maximum):
    def decorator(function):
        @functools.wraps(function)
        def wrapper(*args, **kwargs):
            result = function(*args, **kwargs)
            if result < minimum:
                return minimum
            elif result > maximum:
                return maximum
            return result

        return wrapper

    return decorator


def strictly_typed(function):
    """
    # This decorator requires that every argument and the return value must be
    # annotated with the expected type.
    # Notice that the checking is done only in debug mode (which is Python’s default
    # mode —- controlled by the -O command-line option and the PYTHONOPTIMIZE environment variable).

    :param function:
    :return: decorated function
    """
    annotations = function.__annotations__
    arg_spec = inspect.getfullargspec(function)

    # assert all type is given
    assert 'return' in annotations, 'missing type for return value'
    # arg_spec.args: positional arguments
    # kwonlyargs: keyword only arguments (kwargs after position delimiter sing(*))
    for arg in arg_spec.args + arg_spec.kwonlyargs:
        assert arg in annotations, f'missing type for parameter "{arg}"'

    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        # argument check
        # zip() returns an iterator and dictionary.times() returns a dictionary view
        # we cannot concatenate them directly, so first we convert them both to lists.
        all_args = list(zip(arg_spec.args, args)) + list(kwargs.items())
        for name, arg in all_args:
            assert isinstance(arg, annotations[name]), (
                f'expected argument "{name}" of {annotations[name]} got {type(arg)}')

        # result check
        result = function(*args, **kwargs)
        assert isinstance(result, annotations['return']), (
            f'expected return of {annotations["return"]} got {type(result)}')

        return result

    return wrapper


def coroutine(function):
    @functools.wraps(function)
    def wrapper(*args, **kwargs):
        generator = function(*args, **kwargs)
        next(generator)
        return generator

    return wrapper
