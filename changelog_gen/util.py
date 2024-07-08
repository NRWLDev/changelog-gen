import logging
import time
import typing as t

logger = logging.getLogger(__name__)


def timer(func: t.Callable) -> t.Callable:
    """Timing decorator."""

    def wrapper(*arg, **kw) -> t.Any:  # noqa: ANN401
        t1 = time.time()
        res = func(*arg, **kw)
        t2 = time.time()
        logger.debug("%s %f", func.__name__, (t2 - t1) * 1000)
        return res

    return wrapper
