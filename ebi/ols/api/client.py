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
import inspect

from coreapi import Client

import ebi.ols.api.helpers as helpers
from ebi.ols.api.base import ListClientMixin, DetailClientMixin, HALCodec, SearchClientMixin, site, \
    retry_requests

def_page_size = 1000
logger = logging.getLogger(__name__)


class OlsClient(object):
    """
    Official EMBL/EBI Ontology Lookup Service generic client.
    """

    class ItemClient(object):

        def __init__(self, base_site):
            self.uri = base_site

        def __call__(self, *args, **kwargs):
            item = None
            if len(args) == 1:
                # consider only one args is the requested helper initialized
                item = args[0]
            if 'item' in kwargs:
                item = kwargs.get('item')
            if item:
                if not issubclass(item.__class__, helpers.OLSHelper):
                    raise NotImplementedError('Unable to fin any suitable client for %s', item.__class__.__name__)
                base_uri = 'ontologies/{}'.format(item.ontology_name) if item.ontology_name or kwargs.get(
                    'ontology_name',
                    False) else None
                uri = '/'.join(filter(None, [self.uri, base_uri, item.path]))
                logger.debug('ItemClient uri %s', uri)
                inner_client = DetailClientMixin(uri, item.__class__)
                return inner_client(item.iri)
            else:
                assert ('ontology_name' in kwargs)
                assert ('iri' in kwargs)
                assert ('type' in kwargs)
                item = kwargs.get('type')
                if inspect.isclass(item):
                    assert (issubclass(item, helpers.OLSHelper))
                else:
                    assert (issubclass(item.__class__, helpers.OLSHelper))
                return self.__call__(item=item(ontology_name=kwargs.get('ontology_name'), iri=kwargs.get('iri')))

    @retry_requests
    def __init__(self, page_size=None, base_site=None):
        # Init client from base Api URI
        self.page_size = page_size or def_page_size
        self.site = base_site or site
        document = Client(decoders=[HALCodec()]).get(self.site)
        logger.debug('OlsClient [%s][%s]', document.url, self.page_size)
        # List Clients
        self.ontologies = ListClientMixin('/'.join([self.site, 'ontologies']), helpers.Ontology, document,
                                          self.page_size)
        self.terms = ListClientMixin('/'.join([self.site, 'terms']), helpers.Term, document, self.page_size)
        self.properties = ListClientMixin('/'.join([self.site, 'properties']), helpers.Property, document,
                                          self.page_size)
        self.individuals = ListClientMixin('/'.join([self.site, 'individuals']), helpers.Individual, document,
                                           self.page_size)
        # Details client
        self.ontology = DetailClientMixin('/'.join([self.site, 'ontologies']), helpers.Ontology)
        self.term = DetailClientMixin('/'.join([self.site, 'terms']), helpers.Term)
        self.property = DetailClientMixin('/'.join([self.site, 'properties']), helpers.Property)
        self.individual = DetailClientMixin('/'.join([self.site, 'individuals']), helpers.Individual)
        # Special clients
        self.search = SearchClientMixin('/'.join([self.site, 'search']), helpers.OLSHelper, document, self.page_size)
        self.detail = self.ItemClient(self.site)
