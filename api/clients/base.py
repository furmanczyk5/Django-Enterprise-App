import logging

import requests


logger = logging.getLogger(__name__)


class LogMessages:
    """Standard messages to use for logging"""

    TIMEOUT = "Request to {url} timed out after {timeout} seconds"
    CONNECTION_ERROR = "Network error attempting to connect to {url}"

    ERROR_RESPONSE = "Error response from {url}\nStatus code: {status_code}\nResponse: {response}"


class ExternalService:
    """Base class for external API calls"""

    ACCEPTABLE_METHODS = (
        'get',
        'delete',
        'head',
        'options',
        'patch',
        'post',
        'put',
    )

    def __init__(self, timeout=0.25):
        self.timeout = timeout
        self.api_request = None

    def make_request(self, url, method='get', **kwargs):
        if not isinstance(method, str):
            raise TypeError('`method` must be a string, not {}'.format(type(method)))

        method = method.lower()

        if method not in self.ACCEPTABLE_METHODS:
            raise ValueError('{} is not an acceptable request method\nMust be one of {}'.format(
                method, self.ACCEPTABLE_METHODS
            ))

        try:
            self.api_request = getattr(requests, method)(url, timeout=self.timeout, **kwargs)
        except requests.exceptions.Timeout:
            logger.error(LogMessages.TIMEOUT.format(url=url, timeout=self.timeout))
            return
        except requests.exceptions.ConnectionError:
            logger.error(LogMessages.CONNECTION_ERROR.format(url=url), exc_info=True)
            return
        if self.api_request.status_code >= 400:
            logger.error(LogMessages.ERROR_RESPONSE.format(
                url=url,
                status_code=self.api_request.status_code,
                response=self.api_request.text
            ))
            # The only way to efficiently get the current badge from Credly for mass updates:
            if url.find("credly.com") >= 0 and url.find("/replace") >= 0:
                return self.api_request
            return
        return self.api_request
