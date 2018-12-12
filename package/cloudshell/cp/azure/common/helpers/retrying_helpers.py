import traceback

from msrest.exceptions import ClientRequestError
from msrestazure.azure_exceptions import CloudError
from requests.packages.urllib3.exceptions import ConnectionError


retryable_error_string = "RetryableError"
retryable_error_timeout = 180000
retryable_error_max_attempts = 3


def retry_if_connection_error(exception):
    """Return True if we should retry (in this case when it's an IOError), False otherwise
    :param exception:
    """
    return isinstance(exception, ClientRequestError) or isinstance(exception, ConnectionError) or is_pool_closed_error(
        exception)


def retry_if_retryable_error(exception):
    """Return True if we should retry (in this case when it's an RetryableError), False otherwise
    :param exception:
    """
    return isinstance(exception, CloudError) and (exception.error.__contains__(retryable_error_string) or
                                                  exception.message.__contains__(retryable_error_string))


def is_pool_closed_error(exception):
    execption_message_list = traceback.format_exception_only(type(exception), exception)
    execption_message = "".join(execption_message_list)
    return "pool is closed" in execption_message.lower()
