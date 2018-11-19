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

import coreapi.exceptions
import math
import time
from coreapi import Client, codecs
from hal_codec import HALCodec as OriginCodec
from requests.exceptions import ConnectionError

from ebi.ols.api import exceptions

logger = logging.getLogger(__name__)
__all__ = ['HALCodec', 'DetailClientMixin', 'ListClientMixin',
           'SearchClientMixin', 'site', 'retry_requests']

site = 'https://www.ebi.ac.uk/ols/api'


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
        return urllib.parse.quote_plus(urllib.parse.quote_plus(identifier))


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
            if self.elem_class.path in document.data:
                # the request returned a list of object
                if not silent:
                    logger.warning('OLS returned multiple {}s for {}'.format(self.elem_class.__name__, logger_id))
                # return a list instead
                elms = ListClientMixin(self.uri, self.elem_class, document, 100)
                if not unique:
                    return elms
                else:
                    for elem in elms:
                        if elem.is_defining_ontology:
                            return elem
                    logger.warning('Unable to fin item %s defined in an ontology', logger_id)
                return None
            return self.elem_class(**document.data)
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

    def __init__(self, uri, elem_class, document=None, page_size=1000):
        """
        Initialize a list object
        :param uri: the OLS api base source uri
        :param elem_class: the expected class items objects
        :param: coreapi.Document from api (used to avoid double call to api if already loade elsewhere
        """
        super().__init__(uri, elem_class)
        self.document = document or self.client.get(uri, force_codec='hal')
        self.page_size = page_size
        self.base_uri = document.url if document is not None else uri
        self.index = 0
        logger.debug('ListClientMixin init[%s][%s][%s]', self.elem_class, self.document.url, self.page_size)

    def elem_class_instance(self, **data):
        """
        Get an item object from dedicated class expected object
        :param data:
        :return:
        """
        return self.elem_class(**data)

    @retry_requests
    def __call__(self, filters=None, action=None):
        """
        Allow to search for a list of helpers, retrieve self, wich is now a iterator on the actual list of related
        helpers
        """
        if filters is None:
            filters = {}
        else:
            try:
                check_fn = getattr(self, 'filters_' + self.path)
                if callable(check_fn):
                    filters = check_fn(filters)
            except AttributeError:
                pass
            except AssertionError as e:
                raise exceptions.BadParameter({'error': "Bad Request", 'message': str(e),
                                               'status': 400, 'path': self.path, 'timestamp': time.time()})
            if 'size' in filters:
                self.page_size = filters['size']
        params = {'page': 0, 'size': self.page_size}
        params.update(filters)
        path = action if action else self.path
        self.fetch_document(path, params)
        self.index = 0
        return self

    @retry_requests
    def fetch_document(self, path, params=None):
        """
        Fetch coreapi.Document object fro specified path (based on current loaded document fro base uri
        :param path: related path
        :param params: call params / filters
        :return Document: fetched document from api
        """
        if params is None:
            params = {}
        logger.debug('Action on document %s/%s?%s', self.document.url, path,
                     '&'.join(['%s=%s' % (name, value) for name, value in params.items()]))
        self.document = self.client.action(self.document, [path], params=params, validate=False)
        return self.document

    @retry_requests
    def fetch_page(self, page):
        """
        Fetch document page from paginated results
        :param page: expected page
        :return Document: fetched page document fro api
        """
        uri = '/'.join([self.base_uri, self.path]) + '?page={}&size={}'.format(page, self.page_size)
        logger.debug('Fetch page "%s"', uri)
        self.document = self.client.get(uri, force_codec='hal')
        return self.document

    def __len__(self):
        """
        Current list full length (all elements)
        :return: int
        """
        # # print('len ', self._len, self._len or self.document['page']['totalElements'])
        return self._len or self.document['page']['totalElements']

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
        return self._pages or self.document['page']['totalPages'] - 1

    @pages.setter
    def pages(self, pages):
        self._pages = pages

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

        if self.index < len(self.data):  # and self.index + (self.page * self.page_size) < len(self):
            # Simply return current indexed item
            pass
        elif self.page < self.pages:
            self.fetch_document('next')
            self.index = 0
        else:
            raise StopIteration

        loaded = self.elem_class_instance(**self.data[self.index])
        self.index += 1
        logger.debug('Loaded %s', loaded)
        return loaded

    def __getitem__(self, item):
        """
        Return indexed item, if exists
        :param item: int the current index to get
        :return: item class object
        """
        if isinstance(item, slice):
            logger.debug('Sliced params [%s %s]', item.start, item.stop)
            if item.start > (len(self) - 1) or item.stop > (len(self) - 1):
                raise KeyError('Out of bound indexes %s ', len(self) - 1)

            page = item.start // self.page_size
            logger.debug('Expected page for start %s', page)
            if page != self.page:
                self.fetch_page(page)
            if item.start < item.stop:
                slice_range = range(item.start, item.stop)
                self.index = item.start
            else:
                self.index = item.stop
                slice_range = range(item.start, item.stop, -1)
            logger.debug('Creating slice from [%s - %s]', self.index, slice_range)
            return [self[ii] for ii in slice_range]
        elif isinstance(item, int):
            page = item // self.page_size
            index = item % self.page_size
            logger.debug('Current page %s. %s translated to %s in page %s', self.page, item, index, page)
            if page != self.page:
                self.fetch_page(page)
                self.index = index
            if index > len(self.data):
                raise KeyError("No corresponding key {}".format(item))
            return self.elem_class_instance(**self.data[index])
        else:
            raise TypeError("Key indexes must be int, not {}".format(type(item)))

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
        type_item = kwargs.pop('type')
        if type_item == 'property':
            return helpers.Property(**kwargs)
        elif type_item == 'individual':
            return helpers.Individual(**kwargs)
        elif type_item == 'ontology':
            return helpers.Ontology(**kwargs)
        else:
            return helpers.Term(**kwargs)

    # TODO elem_class as property

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

    @retry_requests
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
            logger.debug('Filter %s:%s', filter_name, filter_value)
            filters_uri += '&' + filter_name + '=' + urllib.parse.quote_plus(filter_value)
        filters_uri += "&exact=on"
        uri += filters_uri
        self.base_search_uri = uri
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
        uri = self.base_search_uri + '&rows={}&start={}'.format(self.page_size, page * self.page_size)
        self.document = self.client.get(uri, format='hal')
        logger.debug('Loaded page %s', self.document.url)
        return self.document


