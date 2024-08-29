import logging

logger = logging.getLogger()


class ClientException(BaseException):
    """
    A custom exception for the SDK client
    """

    ...


class AuthenticationError(ClientException):
    """
    An authentication exception for the SDK client
    """

    ...


class NoResourcesAvailableError(ClientException):
    """
    An exception raised when no resources are available to create new virtual machines
    """

    ...
