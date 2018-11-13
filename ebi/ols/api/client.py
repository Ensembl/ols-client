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

from coreapi import Client

import ebi.ols.api.helpers as helpers
from ebi.ols.api.base import ListClientMixin, DetailClientMixin, ItemClient, HALCodec, SearchClientMixin, site

def_page_size = 1000
logger = logging.getLogger(__name__)


class OlsClient(object):
    """
    Official EMBL/EBI Ontology Lookup Service generic client.
    """

    def __init__(self, page_size=None):
        # Init client from base Api URI
        self.page_size = page_size or def_page_size

        document = Client(decoders=[HALCodec()]).get(site)
        logger.debug('OlsClient [%s][%s]', document.url, self.page_size)
        # List Clients
        self.ontologies = ListClientMixin('/'.join([site, 'ontologies']), helpers.Ontology, document, self.page_size)
        self.terms = ListClientMixin('/'.join([site, 'terms']), helpers.Term, document, self.page_size)
        self.properties = ListClientMixin('/'.join([site, 'properties']), helpers.Property, document, self.page_size)
        self.individuals = ListClientMixin('/'.join([site, 'individuals']), helpers.Individual, document,
                                           self.page_size)
        # Details client
        self.ontology = DetailClientMixin('/'.join([site, 'ontologies']), helpers.Ontology)
        self.term = DetailClientMixin('/'.join([site, 'terms']), helpers.Term)
        self.property = DetailClientMixin('/'.join([site, 'properties']), helpers.Property)
        self.individual = DetailClientMixin('/'.join([site, 'individuals']), helpers.Individual)
        # Special clients
        self.search = SearchClientMixin('/'.join([site, 'search']), helpers.OLSHelper, document)
        self.detail = ItemClient(site, helpers.OLSHelper)
