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
import logging
import urllib.parse
import os
import coreapi.exceptions
import math
import time
from coreapi import Client, codecs
from hal_codec import HALCodec as OriginCodec
from hal_codec import _parse_document as HALParseDocument
from requests.exceptions import ConnectionError

from ebi.ols.api import exceptions

logger = logging.getLogger(__name__)
__all__ = ['HALCodec', 'DetailClientMixin', 'ListClientMixin',
           'SearchClientMixin', 'retry_requests']


def retry_requests(api_func):
    """
    Decorator for retrying calls to API in case of Network issues
    :param api_func: Api client function to call
    :return:
    """
    from itertools import chain

    def call_api(*args, **kwargs):
        call_object = args[0].__class__.__name__
        retry = 1
        max_retry = 5
        while retry <= max_retry:
            trace = "%s.%s(%s)" % (call_object, api_func.__name__,
                                   ", ".join(map(repr, chain(args[1:], kwargs.values()))))
            try:
                logger.debug('Calling client (%s/%s): %s ', retry, max_retry, trace)
                return api_func(*args, **kwargs)
            except (ConnectionError, coreapi.exceptions.CoreAPIException, exceptions.ServerError) as e:
                # wait 5 seconds until next OLS api client try
                logger.warning('Api Error: %s', e)
                logger.warning('Call retry (%s/%s): %s ', retry, max_retry, trace)
                time.sleep(5)
                retry += 1
                if retry > max_retry:
                    logger.error('API unrecoverable error %s', trace)
                    raise exceptions.ObjectNotRetrievedError(e)
            except exceptions.NotFoundException as e:
                # no retry when this is just a 404 error
                logger.error('API unrecoverable error %s', trace)
                raise e
            except exceptions.BadParameter as e:
                logger.error('API call error %s', trace)
                raise e
            except exceptions.BadFilters as e:
                logger.error('API applied filters errors %s', trace)
                raise e

    return call_api


class HALCodec(OriginCodec):
    format = 'hal'


class BaseClient(object):
    decoders = [HALCodec(), codecs.JSONCodec()]

    def __init__(self, uri, elem_class):
        """
        Init from base uri and expected element helper class
        :param uri: relative uri to base OLS url
        :param elem_class: helper class expected
        """
        self.client = Client(decoders=self.decoders)
        self.uri = uri
        self.elem_class = elem_class

    @staticmethod
    def filters_response(filters):
        """ Filters queries for search"""
        logger.debug('Applying filters %s', filters)
        assert set(filters.keys()).issubset(
            {'exact', 'fieldList', 'groupField', 'obsoletes', 'ontology', 'queryFields', 'slim', 'type', 'local'}), \
            "Unauthorized filter key"
        if 'fieldList' in filters:
            if type(filters['fieldList']) is str:
                assertion_set = set(filters['fieldList'].split(','))
            elif type(filters['fieldList'] is set):
                assertion_set = filters['fieldList']
            assert assertion_set.issubset(
                {'description', 'id', 'iri', 'is_defining_ontology', 'label', 'obo_id', 'ontology_name',
                 'ontology_prefix', 'short_form', 'type'}
            ), "Wrong fieldList - check OLS doc"
        if 'queryFields' in filters:
            if type(filters['queryFields']) is str:
                assertion_set = set(filters['queryFields'].split(','))
            elif type(filters['queryFields'] is set):
                assertion_set = filters['queryFields']
            assert assertion_set.issubset(
                {'annotations', 'description', 'iri', 'label', 'logical_description', 'obo_id', 'short_form', 'synonym'}
                ), "Wrong queryFields - check OLS doc"
        if 'type' in filters:
            if type(filters['type']) is str:
                assertion_set = set(filters['type'].split(','))
            elif type(filters['type'] is set):
                assertion_set = filters['type']
            assert assertion_set.issubset({'class', 'property', 'individual', 'ontology', 'term'}), \
                "Wrong type - check OLS doc"
            filters['type'] = filters['type'].replace('term', 'class')
        if 'exact' in filters:
            assert filters['exact'] in ['true', 'false'], '"exact" only accept true|false'
        if 'groupFields' in filters:
            assert filters['groupFields'] in ['true', 'false'], '"groupFields" only accept true|false'
        if 'obsoletes' in filters:
            assert filters['obsoletes'] in ['true', 'false'], '"obsoletes" only accept true|false'
        if 'local' in filters:
            assert filters['local'] in ['true', 'false'], '"local" only accept true|false'
        return filters

    @staticmethod
    def filters_terms(filters):
        """ Check filters for terms queries"""
        logger.debug('Applying filters %s', filters)
        assert set(filters.keys()).issubset({'size', 'iri', 'obo_id', 'short_form'}), "Unauthorized filter key"
        assert len(filters.keys()) <= 1, "Only one filter can be applied at a time"
        return filters

    @staticmethod
    def make_uri(identifier):
        """ Get identifier format for ontologies """
        return urllib.parse.quote_plus(urllib.parse.quote_plus(str(identifier)))

    def elem_class_instance(self, **data):
        """
        Get an item object from dedicated class expected object
        :param data:
        :return:
        """
        return self.elem_class(**data)


class DetailClientMixin(BaseClient):
    """
    Item detailed client, fetch a unique OLS api resource based ont its identifier

    """

    @retry_requests
    def __call__(self, identifier, silent=True, unique=True):
        """ Check one element from OLS API accroding to specified identifier
        In cas API returns multiple element return either:
        - the one which is defining_ontology (flag True)
        - The first one if none (Should not happen)
        """
        iri = self.make_uri(identifier)
        path = "/".join([self.uri, iri])
        logger_id = '[identifier:{}, path:{}]'.format(iri, path)
        logger.debug('Detail client %s [silent:%s, unique:%s]', logger_id, silent, unique)
        try:
            document = self.client.get(path)
            if not isinstance(document, coreapi.document.Document):
                document = coreapi.document.Document(url=path, content=document)
            if self.elem_class.path in document.data:
                # the request returned a list of object
                if not silent:
                    logger.warning('OLS returned multiple {}s for {}'.format(self.elem_class.__name__, logger_id))
                # return a list instead
                elms = ListClientMixin(self.uri, self.elem_class, document, 100)
                if not unique:
                    return elms
                else:
                    return next((x for x in elms if x.is_defining_ontology), elms[0])
            return self.elem_class_instance(**document.data)
        except coreapi.exceptions.ErrorMessage as e:
            if 'status' in e.error:
                if e.error['status'] == 404:
                    raise exceptions.NotFoundException(e.error)
                elif 400 < e.error['status'] < 499:
                    raise exceptions.BadParameter(e.error)
                elif e.error['status'] >= 500:
                    raise exceptions.ServerError(e.error)
            raise exceptions.OlsException(e.error)
        except coreapi.exceptions.CoreAPIException as e:
            raise e


class ListClientMixin(BaseClient):
    """
    List client retrieve items (ontologies, terms, individuals, properties) as list-like object from OLS REST api.
    """
    _pages = None
    _len = None
    page_size = 1000
    current_filters = {}

    def __init__(self, uri, elem_class, document=None, page_size=1000, filters={}, index=0):
        """
        Initialize a list object
        :param uri: the OLS api base source uri
        :param elem_class: the expected class items objects
        :param: coreapi.Document from api (used to avoid double call to api if already loade elsewhere
        """
        self.current_filters = filters
        client_uri = document.url if document is not None else uri
        super().__init__(client_uri, elem_class)
        self.document = document or self.client.get(uri, force_codec=True)
        self.page_size = page_size
        self.index = index
        logger.debug('ListClientMixin init[%s][%s][%s]', self.elem_class, self.document.url, self.page_size)

    @retry_requests
    def __call__(self, filters={}, action=None):
        """
        Allow to search for a list of helpers, retrieve self, wich is now a iterator on the actual list of related
        helpers
        """
        page_size = self.page_size
        if filters:
            try:
                check_fn = getattr(self, 'filters_' + self.path, None)
                if callable(check_fn):
                    filters = check_fn(filters)
            except AssertionError as e:
                raise exceptions.BadFilters(str(e))
            page_size = filters.get('size', self.page_size)
        params = {'page': 0, 'size': page_size}
        params.update(filters)
        path = action if action else self.path
        document = self.fetch_document(path, params, filters)
        obj = self.__class__(path, self.elem_class, document, page_size, filters)
        obj.uri = urllib.parse.urljoin(obj.uri, os.path.dirname(urllib.parse.urlparse(obj.uri).path))
        return obj

    @retry_requests
    def fetch_document(self, path, params=None, filters={}, base_document=None):
        """
        Fetch coreapi.Document object fro specified path (based on current loaded document fro base uri
        :param path: related path
        :param params: call params / filters
        :return Document: fetched document from api
        """
        if params is None:
            params = filters or self.current_filters
        if base_document is None:
            base_document = self.document
        logger.debug('Action on document %s/%s?%s', base_document.url, path,
                     '&'.join(['%s=%s' % (name, value) for name, value in params.items()]))
        document = self.client.action(base_document, path, params=params, validate=False)
        if not isinstance(document, coreapi.document.Document):
            document = HALParseDocument(document)
        return document

    @retry_requests
    def fetch_page(self, page):
        """
        Fetch document page from paginated results
        :param page: expected page
        :return Document: fetched page document fro api
        """
        uri = '/'.join([self.uri, self.path]) + '?page={}&size={}'.format(page, self.page_size)
        logger.debug('Fetch page "%s"', uri)
        return self.client.get(uri, force_codec=True)

    @property
    def path(self):
        """ List elements in HAL documents are expected to be inside a path
        ;:return the expected path from item element class
        """
        return self.elem_class.path

    def _get_page(self, document):
        return document['page']['number']

    @property
    def page(self):
        """
        Current page
        :return: int
        """
        return self._get_page(self.document)

    def _get_pages(self, document):
        return document['page']['totalPages']

    @property
    def pages(self):
        """
        Total pages from last api request
        :return: int
        """
        return self._pages or self._get_pages(self.document)

    @pages.setter
    def pages(self, pages):
        self._pages = pages

    def _get_data(self, path, document):
        if path in document:
            return document.data[path]

    @property
    def data(self):
        """ Current object pages elements list
        :return list
        """
        data = self._get_data(self.path, self.document)
        return data if data else []

    def __len__(self):
        """
        Current list full length (all elements)
        :return: int
        """
        # # print('len ', self._len, self._len or self.document['page']['totalElements'])
        return self._len or self.document['page']['totalElements']

    def _gen_elems_forward(self, begin, end):
        page = begin // self.page_size
        if page != self.page:
            document = self.fetch_page(page)
        else:
            document = self.document

        index = begin % self.page_size
        while begin < end:
            if index >= len(self._get_data(self.path, document)):
                index = 0
                document = self.fetch_document('next',
                                               filters=self.current_filters,
                                               base_document=document)

            data = self._get_data(self.path, document)[index]
            yield self.elem_class_instance(**data)
            index += 1
            begin += 1

    def __iter__(self):
        """
        Iter elements in current list, if outbound current pages items, load next page
        :return: generator
        """
        index = self.index
        return self._gen_elems_forward(index, len(self))

    def __getitem__(self, item):
        """
        Return indexed item, if exists
        :param item: int the current index to get
        :return: item class object
        """
        if isinstance(item, slice):
            logger.debug('Sliced params [%s %s]', item.start, item.stop)
            if item.start > len(self) or item.stop > len(self):
                raise IndexError('Out of bound indexes. Container len: %s ', len(self))

            logger.debug('Creating slice from [%s - %s]', item.start, item.stop)
            if item.start < item.stop:
                return [elem for elem in self._gen_elems_forward(item.start, item.stop)]
            else:
                list_slice = [elem for elem in self._gen_elems_forward(item.stop, item.start)]
                list_slice.reverse()
                return list_slice
        elif isinstance(item, int):
            index = item % self.page_size
            if index >= len(self):
                raise IndexError("No corresponding key {}".format(item))
            page = item // self.page_size
            document = self.document
            if page != self.page:
                document = self.fetch_page(page)

            data = self._get_data(self.path, document)[index]
            return self.elem_class_instance(**data)
        else:
            raise TypeError("Key indexes must be int, not {}".format(type(item)))

    def __repr__(self):
        """ String repr of list
        :return str
        """
        return self.__class__.__name__ + '([' + ', '.join([repr(self.elem_class_instance(**data)) for data in self.data]) + '])'


class SearchClientMixin(ListClientMixin):
    """
    Mixed items classes list, retrieved from search endpoint in OLS REST api

    """
    path = 'response'

    def __call__(self, query=None, filters={}, **kwargs):
        """

        :param filters: filters to apply to search
        :param query: searched string
        :return: a list of mixed items (individuals, ontologies, terms, properties)
        """
        if query is None:
            raise exceptions.BadParameter({'error': "Bad Request", 'message': 'Missing query',
                                           'status': 400, 'path': 'search', 'timestamp': time.time()})
        self.query = query
        call_filters = filters or {key: value for key, value in kwargs.items()} or {}
        obj = super().__call__(call_filters)
        obj.query = query
        return obj

    def __len__(self):
        return self.document[self.path]['numFound']

    def elem_class_instance(self, **kwargs):
        """
        Search OLS api returns mixed types elements, get current element class to return accordingly
        :param kwargs: type items
        :return: mixed
        """
        import ebi.ols.api.helpers as helpers
        type_item = kwargs.pop('type', None)
        if type_item == 'property':
            return helpers.Property(**kwargs)
        elif type_item == 'individual':
            return helpers.Individual(**kwargs)
        elif type_item == 'ontology':
            return helpers.Ontology(**kwargs)
        else:
            return helpers.Term(**kwargs)

    # TODO elem_class as property

    def _get_start(self, document):
        return document[self.path]['start']

    @property
    def start(self):
        """ First element index in full list
        """
        return self._get_start(self.document)

    def _get_page(self, document):
        return math.floor(self._get_start(document) / self.page_size)

    @property
    def page(self):
        """ Calculate current page, not returned directly from api
        :return int
        """
        return self._get_page(self.document)

    def _get_pages(self, _document=None):
        return math.ceil(len(self) / self.page_size)

    @property
    def pages(self):
        """ Calculate and return search pages number
        :return int
        """
        return self._get_pages()

    def _get_data(self, path, document):
        return document.data[path]['docs']

    @property
    def data(self):
        """ Actual list elements from returned search elements
        """
        return self._get_data(self.path, self.document)

    def _get_base_uri(self, params=None, filters={}):
        if params is None:
            params = filters or self.current_filters
        params.pop('page', 0)
        params.pop('size', 0)
        uri = '/'.join([self.uri, 'search'])
        uri += '?q=' + self.query
        filters_uri = ''
        for filter_name, filter_value in params.items():
            logger.debug('Filter %s:%s', filter_name, filter_value)
            if isinstance(filter_value, set):
                filters_uri += '&' + filter_name + '=' + ','.join(filter_value)
            else:
                filters_uri += '&' + filter_name + '=' + filter_value
        uri += filters_uri
        return uri

    @retry_requests
    def fetch_document(self, path, params=None, filters={}, base_document=None):
        """
        Fetch current search elements
        :param path: the uri relative path
        :param params: search params
        :return: Document
        """
        if base_document:
            self.document = base_document
        start = 0 if path != 'next' else self.start + self.page_size
        uri = self._get_base_uri(params, filters)
        final_uri = uri + '&rows={}&start={}'.format(self.page_size, start)
        logger.debug('Final uri %s', final_uri)
        self.document = self.client.get(final_uri, format='hal')
        logger.debug('Loaded document from %s', self.document.url)
        return self.document

    @retry_requests
    def fetch_page(self, page):
        """ Fetch OLS api search page
        :return Document
        """
        base_uri = self._get_base_uri()
        uri = base_uri + '&rows={}&start={}'.format(self.page_size, page * self.page_size)
        self.document = self.client.get(uri, format='hal')
        logger.debug('Loaded page %s', self.document.url)
        return self.document
