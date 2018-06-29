# -*- coding: utf-8 -*-


class OlsException(Exception):
    """
    A base class for all `OLS` exceptions.
    """
    def __init__(self, error):
        self.error = error

    def __repr__(self):
        return '%s(%s)' % (self.__class__.__name__, repr(self.error))

    def __str__(self):
        return str(self.error)


class NotFoundException(OlsException):
    """
    Entity was not found via a OLS api call
    """
    pass


class BadParameter(OlsException):
    """
    Passed parameters does not fit with expected
    """
    pass

