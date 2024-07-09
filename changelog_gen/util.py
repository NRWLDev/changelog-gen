import logging
import time
import typing as t

logger = logging.getLogger(__name__)


def timer(func: t.Callable) -> t.Callable:
    """Timing decorator."""

    def wrapper(*arg, **kw) -> t.Any:  # noqa: ANN401
        t1 = time.time_ns()
        try:
            res = func(*arg, **kw)
        finally:
            t2 = time.time_ns()
            logger.debug("%s %fms", func.__name__, (t2 - t1) / 1000000)
        return res

    return wrapper
