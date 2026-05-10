from collections.abc import Callable
from typing import ParamSpec, TypeVar

from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential_jitter

P = ParamSpec("P")
T = TypeVar("T")


def retry_external_call[P, T](fn: Callable[P, T]) -> Callable[P, T]:
    return retry(
        retry=retry_if_exception_type((TimeoutError, ConnectionError)),
        wait=wait_exponential_jitter(initial=0.25, max=3),
        stop=stop_after_attempt(3),
        reraise=True,
    )(fn)
