# -*- coding: utf-8 -*-
"""
.. See the NOTICE file distributed with this work for additional information
   regarding copyright ownership.
   Licensed under the Apache License, Version 2.0 (the "License");
   you may not use this file except in compliance with the License.
   You may obtain a copy of the License at
       http://www.apache.org/licenses/LICENSE-2.0
   Unless required by applicable law or agreed to in writing, software
   distributed under the License is distributed on an "AS IS" BASIS,
   WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
   See the License for the specific language governing permissions and
   limitations under the License.
"""


class OlsException(Exception):
    """
    A base class for all `OLS` exceptions.
    """

    def __init__(self, error, uri=None):
        self.error = error['message'] if 'message' in error else None
        self.status = error['status'] if 'status' in error else None
        self.origin = error['exception'] if 'exception' in error else None
        self.timestamp = error['timestamp'] if 'timestamp' in error else None
        self.uri = uri

    def __repr__(self):
        return '{}({}) [{}-{}]{%s}'.format(self.origin, self.status, self.timestamp, self.error, self.uri)

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


class ServerError(OlsException):
    """
    Convenient class for OLS server Errors
    """
    pass