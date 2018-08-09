# -*- coding: utf-8 -*-
import math
import sys
import time
import urllib.parse
import warnings

from coreapi import codecs, Client
from coreapi.exceptions import ErrorMessage

from ebi.ols.api import exceptions
from ebi.ols.api.codec import HALCodec


decoders = [HALCodec(), codecs.JSONCodec()]
site = 'https://www.ebi.ac.uk/ols/api'


def filters_ontologies(filters):
    return filters or {}


def filters_response(filters):
    assert set(filters.keys()).issubset(
        {'ontology', 'type', 'slim', 'queryFields', 'exact', 'fieldList', 'groupField', 'obsoletes',
         'local'}) or len(filters) == 0, "Unauthorized filter key"
    if 'fieldList' in filters:
        assert (set(filters['fieldList'].keys().issubset(
            {'iri', 'ontology_name', 'ontology_prefix', 'short_form', 'description', 'id', 'label',
             'is_defining_ontology', 'obo_id', 'type'}
        )))
    if 'queryFields' in filters:
        assert (set(filters['queryFields'].keys().issubset(
            {'label', 'synonym', 'description', 'short_form', 'obo_id', 'annotations', 'logical_description',
             'iri'}
        )))
    if 'type' in filters:
        assert (set(filters['type'].keys().issubset(
            {'class', 'property', 'individual', 'ontology'}
        )))
    if 'exact' in filters:
        assert (filters['exact'] in ['true', 'false'])
    if 'groupFields' in filters:
        assert (filters['groupFields'] in ['true', 'false'])
    if 'obsoletes' in filters:
        assert (filters['obsoletes'] in ['true', 'false'])
    if 'local' in filters:
        assert (filters['local'] in ['true', 'false'])
    return filters


def filters_terms(filters):
    assert set(filters.keys()).issubset({'iri', 'obo_id', 'short_form'}), "Unauthorized filter key"
    assert len(filters.keys()) <= 1, "Only one filter can be applied at a time"
    return filters


def uri_ontologies(identifier):
    return identifier


def uri_terms(identifier):
    return urllib.parse.quote_plus(urllib.parse.quote_plus(identifier))


def uri_individuals(identifier):
    return urllib.parse.quote_plus(urllib.parse.quote_plus(identifier))


def uri_properties(identifier):
    return urllib.parse.quote_plus(urllib.parse.quote_plus(identifier))


class BaseClient(object):

    def __init__(self):
        self.client = Client(decoders=decoders)


class DetailClientMixin(BaseClient):

    def __init__(self, uri, elem_class):
        super().__init__()
        self.uri = uri
        self.elem_class = elem_class

    def __call__(self, identifier, silent=False):
        """ Check one element from OLS API accroding to specified identifier
        In cas API returns multiple element return either:
        - the one which is defining_ontology (flag True)
        - The first one if none (Should not happen)
        """
        identifier_fn = getattr(sys.modules[__name__], 'uri_' + self.elem_class.path)
        path = "/".join([site, self.uri, identifier_fn(identifier)])
        try:
            document = self.client.get(path)
            # print('current path', self.elem_class, path)
            if self.elem_class.path in document.data:
                # the request returned a list of object
                if not silent:
                    warnings.warn(
                        'OLS returned multiple {}s for {}'.format(self.elem_class.__name__, identifier))
                # return a list instead
                return ListClientMixin(self.uri, self.elem_class, document)
            return self.elem_class(**document.data)
        except ErrorMessage as e:
            # print(e.error)
            raise exceptions.OlsException(e.error)


class ListClientMixin(BaseClient):
    page_size = 100

    def __init__(self, uri, elem_class, document=None):
        super().__init__()
        self.document = document or self.client.get('/'.join([site, uri]), force_codec='hal')
        self.elem_class = elem_class
        self.index = 0

    def elem_class_instance(self, **data):
        return self.elem_class(**data)

    def __call__(self, filters=None, action=None):
        """
        Allow to search for a list of helpers, retrieve self, wich is now a iterator on the actual list of related
        helpers
        """
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
            raise exceptions.BadParameter({'error': "Bad Request", 'message': str(e),
                                           'status': 400, 'path': self.path, 'timestamp': time.time()})

        params.update(filters)
        path = action if action else self.path
        self.fetch_document(path, params)
        self.index = 0

        return self

    def fetch_document(self, path, params=None):
        if params is None:
            params = {}
        self.document = self.client.action(self.document, [path], params=params, validate=False)

    def fetch_page(self, page):
        self.document = self.client.get(
            '/'.join([site, self.path]) + '?page={}&size={}'.format(page, self.page_size),
            force_codec='hal')

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
    def pages(self):
        return self.document['page']['totalPages'] - 1

    @property
    def data(self):
        if self.path in self.document:
            return self.document.data[self.path]
        return []

    def __next__(self):
        if self.index < len(self.data):
            # Simply return current indexed item
            pass
        elif self.page < self.pages:
            self.fetch_document('next')
            # self.document = self.client.action(self.document, ['next'])
            self.index = 0
        else:
            raise StopIteration
        loaded = self.elem_class_instance(**self.data[self.index])
        self.index += 1
        return loaded

    def __getitem__(self, item):
        if isinstance(item, slice):
            return [self[ii] for ii in range(*item.indices(len(self)))]
        if type(item) is not int:
            raise TypeError("Key indexes must be int, not {}".format(type(item)))
        if item > (len(self) - 1):
            # TODO relace with proper ArrayError Text
            raise KeyError("No corresponding key {}".format(item))
        else:
            page = item // self.page_size
            index = item % self.page_size
            if page == self.page:
                return self.elem_class_instance(**self.data[index])
            else:
                self.fetch_page(page)
                self.index = index
                return self.elem_class_instance(**self.data[index])

    def __repr__(self) -> str:
        return '[' + ','.join([repr(self.elem_class_instance(**data)) for data in self.data]) + ']'



class SearchClientMixin(ListClientMixin):
    base_search_uri = ''

    def __call__(self, filters=None, query=None):
        if query is None:
            raise exceptions.BadParameter({'error': "Bad Request", 'message': 'Missing query',
                                           'status': 400, 'path': 'search', 'timestamp': time.time()})
        self.query = query  #
        return super().__call__(filters)

    def __len__(self):
        return self.document[self.path]['numFound']

    def elem_class_instance(self, **kwargs):
        import ebi.ols.api.helpers as helpers
        type_item = kwargs.get('type')
        if type_item == 'property':
            return helpers.Property(**kwargs)
        elif type_item == 'individual':
            return helpers.Individual(**kwargs)
        elif type_item == 'ontology':
            return helpers.Ontology(**kwargs)
        else:
            return helpers.Term(**kwargs)

    @property
    def start(self):
        return self.document[self.path]['start']

    @property
    def path(self):
        return 'response'

    @property
    def page(self):
        return math.floor(self.start / self.page_size) + 1

    @property
    def pages(self):
        return math.ceil(len(self) / self.page_size)

    @property
    def data(self):
        return self.document.data[self.path]['docs']

    def fetch_document(self, path, params=None):
        if params is None:
            params = {}
        params.pop('page', 0)
        params.pop('size', 0)
        start = 0 if path != 'next' else self.start + self.page_size
        uri = '/'.join([site, 'search'])
        uri += '?q=' + self.query
        filters_uri = ''
        for filter_name, filter_value in params.items():
            # print(filter_name, filter_value)
            filters_uri += '&' + filter_name + '=' + urllib.parse.quote_plus(filter_value)
        filters_uri += "&exact=on"
        uri += filters_uri + '&rows=100&start={}'.format(start)
        self.base_search_uri = uri
        # print('Search uri', uri)
        self.document = self.client.get(uri, format='hal')

    def fetch_page(self, page):
        uri = self.base_search_uri + '&rows=100&start={}'.format(page * self.page_size)
        self.document = self.client.get(uri, format='hal')
