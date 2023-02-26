import logging
import functools
import os
import tempfile


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


if __name__ == '__main__':

    @logged()
    def say_word(word='hello'):
        return word


    @logged()
    def divide():
        return 1 / 0


    say_word()
    divide()
