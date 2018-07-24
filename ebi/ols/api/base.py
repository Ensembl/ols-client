# -*- coding: utf-8 -*-
import sys
import time
import urllib.parse

from coreapi.exceptions import ErrorMessage
from coreapi import codecs, Client

from ols.api import exceptions, helpers
from ols.api.codec import HALCodec

decoders = [HALCodec(), codecs.JSONCodec()]
site = 'https://www.ebi.ac.uk/ols/api'


def filters_ontologies(filters):
    return filters or {}


def filters_terms(filters):
    assert set(filters.keys()).issubset({'iri', 'obo_id', 'short_form'}), "Unauthorized filter key"
    assert len(filters.keys()) <= 1, "Only one filter can be applied at a time"
    return filters


def uri_ontologies(identifier):
    return identifier


def uri_terms(identifier):
    return urllib.parse.quote_plus(urllib.parse.quote_plus(identifier))


class BaseClient(object):

    def __init__(self):
        self.client = Client(decoders=decoders)


class DetailClientMixin(BaseClient):

    def __init__(self, uri, elem_class):
        super().__init__()
        self.uri = uri
        self.elem_class = elem_class

    def __call__(self, identifier):
        identifier_fn = getattr(sys.modules[__name__], 'uri_' + self.elem_class.path)
        path = "/".join([site, self.uri, identifier_fn(identifier)])
        try:
            document = self.client.get(path)
            return self.elem_class(data=document)
        except ErrorMessage as e:
            raise exceptions.OlsException(e.error)


class ListClientMixin(BaseClient):
    page_size = 100

    def __init__(self, uri, elem_class, document=None):
        super().__init__()
        self.document = document or self.client.get('/'.join([site, uri]), force_codec='hal')
        self.elem_class = elem_class
        self.index = 0

    def __call__(self, filters=None):
        if filters is None:
            filters = {}
        params = {'page': 0, 'size': self.page_size}
        try:
            check_fn = getattr(sys.modules[__name__], 'filters_' + self.path)
            if callable(check_fn):
                filters = check_fn(filters)
        except AttributeError:
            pass
        except AssertionError as e:
            raise exceptions.BadParameter(helpers.Error(error="Bad Request", message=str(e), status=400,
                                                        path=self.path, timestamp=time.time()))

        params.update(filters)
        self.document = self.client.action(self.document, [self.path], params=params, validate=False)
        self.index = 0
        return self

    def __len__(self):
        return self.document['page']['totalElements']

    def __iter__(self):
        return self

    @property
    def path(self):
        return self.elem_class.path

    @property
    def page(self):
        return self.document['page']['number']

    @property
    def n_elements(self):
        return self.document['page']['totalElements']

    @property
    def pages(self):
        return self.document['page']['totalPages']

    @property
    def data(self):
        return self.document.data[self.path]

    def __next__(self):
        if self.index < len(self.data):
            # Simply return current indexed item
            pass
        elif self.page < self.pages - 1:
            self.document = self.client.action(self.document, ['next'])
            self.index = 0
        else:
            raise StopIteration
        loaded = self.elem_class(data=self.data[self.index])
        self.index += 1
        return loaded

    def __getitem__(self, item):
        if type(item) is not int:
            raise TypeError("Key indexes must be int, not {}".format(type(item)))
        if item > self.n_elements - 1:
            # TODO relace with proper ArrayError Text
            raise KeyError("No corresponding key {}".format(item))
        else:
            page = item // self.page_size
            index = item % self.page_size
            if page == self.page:
                return self.elem_class(data=self.data[index])
            else:
                self.document = self.client.get(
                    '/'.join([site, self.path]) + '?page={}&size={}'.format(page, self.page_size),
                    force_codec='hal')
                self.index = index
                return self.elem_class(data=self.data[index])
