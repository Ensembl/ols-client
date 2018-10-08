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
import sys
import urllib.parse
import warnings

import math
import time
from coreapi import codecs, Client
from coreapi.exceptions import ErrorMessage

from ebi.ols.api import exceptions
from ebi.ols.api.codec import HALCodec

decoders = [HALCodec(), codecs.JSONCodec()]
site = 'https://www.ebi.ac.uk/ols/api'


def filters_ontologies(filters):
    """ Filters queries for ontologies (in fact none)"""
    return filters or {}


def filters_response(filters):
    """ Filters queries for search"""
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
    """ Check filters for terms queries"""
    assert set(filters.keys()).issubset({'iri', 'obo_id', 'short_form'}), "Unauthorized filter key"
    assert len(filters.keys()) <= 1, "Only one filter can be applied at a time"
    return filters


def uri_ontologies(identifier):
    """ Get identifier format for ontologies """
    return identifier


def uri_terms(identifier):
    """ Get identifier format for terms (doubled encoded uri) """
    return urllib.parse.quote_plus(urllib.parse.quote_plus(identifier))


def uri_individuals(identifier):
    """ Get identifier format for individuals (doubled encoded uri) """
    return urllib.parse.quote_plus(urllib.parse.quote_plus(identifier))


def uri_properties(identifier):
    """ Get identifier format for properties (doubled encoded uri) """
    return urllib.parse.quote_plus(urllib.parse.quote_plus(identifier))


class BaseClient(object):

    def __init__(self):
        self.client = Client(decoders=decoders)


class DetailClientMixin(BaseClient):
    """
    Item detailed client, fetch a unique OLS api resource based ont its identifier

    """

    def __init__(self, uri, elem_class):
        """
        Init from base uri and expected element helper class
        :param uri: relative uri to base OLS url
        :param elem_class: helper class expected
        """
        super().__init__()
        self.uri = uri
        self.elem_class = elem_class

    def __call__(self, identifier, silent=False, unique=False):
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
                    warnings.warn('OLS returned multiple {}s for {}'.format(self.elem_class.__name__, identifier))
                # return a list instead
                if not unique:
                    return ListClientMixin(self.uri, self.elem_class, document)
                for elem in document.data[self.elem_class.path]:
                    if 'is_defining_ontology' in elem and elem['is_defining_ontology']:
                        return self.elem_class(**elem)
                return None
            return self.elem_class(**document.data)
        except ErrorMessage as e:
            # print(e.error)
            raise exceptions.OlsException(e.error)


class ListClientMixin(BaseClient):
    """
    List client retrieve items (ontologies, terms, individuals, properties) as list-like object from OLS REST api.

    TODO: implement __getslice__
    TODO: review error management
    """
    page_size = 1000

    def __init__(self, uri, elem_class, document=None):
        """
        Initialize a list object
        :param uri: the OLS api base source uri
        :param elem_class: the expected class items objects
        :param: coreapi.Document from api (used to avoid double call to api if already loade elsewhere
        """
        super().__init__()
        self.document = document or self.client.get('/'.join([site, uri]), force_codec='hal')
        # print(self.document)
        self.elem_class = elem_class
        self.base_uri = self.path if document is not None else uri
        # print('base uri set to ', self.base_uri)
        self.index = 0

    def elem_class_instance(self, **data):
        """
        Get an item object from dedicated class expected object
        :param data:
        :return:
        """
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
        """
        Fetch coreapi.Document object fro specified path (based on current loaded document fro base uri
        :param path: related path
        :param params: call params / filters
        :return Document: fetched document from api
        """
        if params is None:
            params = {}
        self.document = self.client.action(self.document, [path], params=params, validate=False)
        return self.document

    def fetch_page(self, page):
        """
        Fetch document page from paginated results
        :param page: expected page
        :return Document: fetched page document fro api
        """
        self.document = self.client.get(
            '/'.join([site, self.base_uri, self.path]) + '?page={}&size={}'.format(page, self.page_size),
            force_codec='hal')
        return self.document

    def __len__(self):
        """
        Current list full length (all elements)
        :return: int
        """
        return self.document['page']['totalElements']

    def __iter__(self):
        """
        Initialize self contained iterator
        :return:
        """
        return self

    @property
    def path(self):
        """ List elements in HAL documents are expected to be inside a path
        ;:return the expected path from item element class
        """
        return self.elem_class.path

    @property
    def page(self):
        """
        Current page
        :return: int
        """
        return self.document['page']['number']

    @property
    def pages(self):
        """
        Total pages from last api request
        :return: int
        """
        return self.document['page']['totalPages'] - 1

    @property
    def data(self):
        """ Current object pages elements list
        :return list
        """
        if self.path in self.document:
            return self.document.data[self.path]
        return []

    def __next__(self):
        """
        Next element in current list, if outbound current pages items, load next page
        :return: list
        """
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
        """
        Return indexed item, if exists
        :param item: int the current index to get
        :return: item class object
        """
        if isinstance(item, slice):
            page = item.start // self.page_size
            self.fetch_page(page)
            self.index = item.start
            return [self[ii] for ii in
                    range(self.index, self.index + max(item.start - item.stop, item.stop - item.start))]
        if type(item) is not int:
            raise TypeError("Key indexes must be int, not {}".format(type(item)))
        if item > (len(self) - 1):
            raise KeyError("No corresponding key {}".format(item))
        else:
            page = item // self.page_size
            index = item % self.page_size
            if page == self.page:
                # print('still in range ')
                return self.elem_class_instance(**self.data[index])
            else:
                # print('out of range, fetch')
                self.fetch_page(page)
                self.index = index
                return self.elem_class_instance(**self.data[index])

    def __repr__(self):
        """ String repr of list
        :return str
        """
        return '[' + ','.join([repr(self.elem_class_instance(**data)) for data in self.data]) + ']'


class SearchClientMixin(ListClientMixin):
    """
    Mixed items classes list, retrieved from search endpoint in OLS REST api

    """
    base_search_uri = ''
    path = 'response'

    def __call__(self, filters=None, query=None):
        """

        :param filters: filters to apply to search
        :param query: searched string
        :return: a list of mixed items (individuals, ontologies, terms, properties)
        """
        if query is None:
            raise exceptions.BadParameter({'error': "Bad Request", 'message': 'Missing query',
                                           'status': 400, 'path': 'search', 'timestamp': time.time()})
        self.query = query  #
        return super().__call__(filters)

    def __len__(self):
        return self.document[self.path]['numFound']

    def elem_class_instance(self, **kwargs):
        """
        Search OLS api returns mixed types elements, get current element class to return accordingly
        :param kwargs: type items
        :return: mixed
        """
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
        """ First element index in full list
        """
        return self.document[self.path]['start']

    @property
    def page(self):
        """ Calculate current page, not returned directly from api
        :return int
        """
        return math.floor(self.start / self.page_size) + 1

    @property
    def pages(self):
        """ Calculate and return search pages number
        :return int
        """
        return math.ceil(len(self) / self.page_size)

    @property
    def data(self):
        """ Actual list elements from returned search elements
        """
        return self.document.data[self.path]['docs']

    def fetch_document(self, path, params=None):
        """
        Fetch current search elements
        :param path: the uri relative path
        :param params: search params
        :return: Document
        """
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
        uri += filters_uri
        self.base_search_uri = uri
        final_uri = uri + '&rows={}&start={}'.format(self.page_size, start)
        self.document = self.client.get(final_uri, format='hal')
        return self.document

    def fetch_page(self, page):
        """ Fetch OLS api search page
        :return Document
        """
        uri = self.base_search_uri + '&rows={}&start={}'.format(self.page_size, page * self.page_size)
        self.document = self.client.get(uri, format='hal')
        return self.document

