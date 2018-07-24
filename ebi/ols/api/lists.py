# -*- coding: utf-8 -*-
import time

import math
from coreapi import Document
from coreapi import Client

import ebi.ols.api.exceptions as exceptions
import ebi.ols.api.helpers as helpers
import ebi.ols.api.utils as utils
from ebi.ols.api.codec import HALCodec

decoders = [HALCodec()]


class SearchTermsList(object):
    path = 'response'

    def _init_page(self, document):

        try:
            # Data in the page
            self._data = document[self.path]['docs']
            self.current = 0
            self.page_size = len(self._data)
            self.total = document[self.path]['numFound']
            self.start = document[self.path]['start']
            self.nb_pages = math.ceil(self.total / self.rows)
            self.page_index = math.floor(self.start / self.page_size) + 1
        except KeyError:
            raise exceptions.OlsException(helpers.Error(error="Data Error", message="No page information", status=500,
                                                        path=self.path, timestamp=time.time()))

    def _item_to_object(self, item):
        return utils.load_data(helpers.Term, item)

    @property
    def has_next_page(self) -> bool:
        return self.current < self.nb_pages

    def __init__(self, parent, current: Document, query, filters, rows, start) -> None:
        # Keep track of parent client for urls and actions
        self.client = parent
        self.filters = filters
        self.query = query
        self.rows = rows
        self.page_document = current
        # Current document
        self._init_page(current)

    def __len__(self):
        return self.total

    def __iter__(self):
        return self

    def __next__(self):
        if self.current < self.page_size:
            loaded = self._item_to_object(self._data[self.current])
        elif self.page_index < self.nb_pages:
            next_step = self.start + self.page_size
            terms_list = self.client.search(self.query, self.filters, self.rows, self.start + self.page_size)
            self._init_page(terms_list.page_document)
            loaded = self._item_to_object(self._data[self.current])
        else:
            raise StopIteration
        self.current += 1
        return loaded
