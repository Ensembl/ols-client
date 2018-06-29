# -*- coding: utf-8 -*-
import time

from coreapi import Document, Client

import ebi.ols.api.exceptions as exceptions
import ebi.ols.api.helpers as helpers

import ebi.ols.api.utils as utils


class ListMixin(object):
    """
    Paginated list results iterator class
    """
    path = None

    def __init__(self, parent, current: Document) -> None:
        # Keep track of parent client for urls and actions
        self.client = parent.client
        # Current document
        self._page_document = current
        # Data in the page
        self._data = current.data[self.path]
        # Set whether
        self._started = False
        # Set up actual data for iteration
        self._init_page()

    def _init_page(self):
        try:
            self.current = 0
            self.max_page = len(self._page_document[self.path])
            self.nb_pages = self._page_document.get('page').get('totalPages')
            self.total = self._page_document.get('page').get('totalElements')
            self.page_size = self._page_document.get('page').get('size')
            self.page_index = self._page_document.get('page').get('number')
        except KeyError:
            raise exceptions.OlsException(helpers.Error(error="Data Error", message="No page information", status=500,
                                                        path=self.path, timestamp=time.time()))

    def __len__(self):
        return self.total

    def __iter__(self):
        return self

    def __next__(self):
        if self.current < self.max_page:
            loaded = self._item_to_object(self._data[self.current])
            self.current += 1
            return loaded
        elif self.has_next_page and self.page_index <= self.nb_pages:
            self._load_page('next')
            loaded = self._item_to_object(self._data[self.current])
            self.current += 1
            return loaded
        else:
            raise StopIteration

    def _load_page(self, link):
        self._page_document = self.client.action(self._page_document, [link])
        self._data = self._page_document.data[self.path]
        self._init_page()

    def current_page(self):
        return self._items_to_objects()

    def next_page(self):
        if self.has_next_page:
            self._load_page('next')
            return self.current_page()
        raise exceptions.BadParameter(helpers.Error(error="Bad Request", message="No next_page item", status=400,
                                                    path=self.path, timestamp=time.time()))

    def prev_page(self):
        if self.has_prev_page:
            self._load_page('prev')
            return self.current_page()
        raise exceptions.BadParameter(helpers.Error(error="Bad Request", message="No previous page", status=400,
                                                    path=self.path, timestamp=time.time()))

    def last_page(self):
        if self.has_last_page:
            self._load_page('last')
            return self.current_page()
        raise exceptions.BadParameter(helpers.Error(error="Bad Request", message="No last page", status=400,
                                                    path=self.path, timestamp=time.time()))

    def first_page(self):
        if self.has_first_page:
            self._load_page('first')
            return self.current_page()
        raise exceptions.BadParameter(helpers.Error(error="Bad Request", message="No first item", status=400,
                                                    path=self.path, timestamp=time.time()))

    @property
    def has_next_page(self) -> bool:
        return 'next' in self._page_document.links

    @property
    def has_first_page(self) -> bool:
        return 'first' in self._page_document.links

    @property
    def has_last_page(self) -> bool:
        return 'last' in self._page_document.links

    @property
    def has_prev_page(self) -> bool:
        return 'prev' in self._page_document.links

    def _items_to_objects(self):
        if self.path not in self._page_document:
            raise exceptions.NotFoundException(helpers.Error("No data", "No data available", 400, None, None))
        else:
            return [self._item_to_object(onto) for onto in self._data]

    def _item_to_object(self, item):
        raise NotImplementedError()


class OntologyList(ListMixin):
    path = "ontologies"

    def _item_to_object(self, item):
        converted = utils.convert_keys(item)
        config = converted.pop("config", None)
        onto_config = utils.load_ontology_config(config)
        ontology = helpers.Ontology(**converted, config=onto_config)
        return ontology


class TermList(ListMixin):
    path = "terms"

    def _item_to_object(self, item):
        return utils.load_data(helpers.Term, item)
