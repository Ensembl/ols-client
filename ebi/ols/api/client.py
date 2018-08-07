# -*- coding: utf-8 -*-

from coreapi import Client

import ebi.ols.api.helpers as helpers
from ebi.ols.api.base import decoders, site, DetailClientMixin, ListClientMixin, SearchClientMixin


class OlsClient(object):
    """
    TODO: add individuals and properties services
    OLS Client ontologies client

    """
    class DetailClient(object):

        def __call__(self, item):
            if isinstance(item, helpers.Property):
                client = DetailClientMixin('properties', helpers.Property)
                return client(item.iri)
            elif isinstance(item, helpers.Individual):
                client = DetailClientMixin('individuals', helpers.Ontology)
            elif isinstance(item, helpers.Ontology):
                client = DetailClientMixin('ontologies', helpers.Ontology)
            else:
                client = DetailClientMixin('terms', helpers.Term)
            return client(item.iri)

    def __init__(self):
        self.client = Client(decoders=decoders)
        document = self.client.get(site)
        self.ontologies = ListClientMixin('ontologies', helpers.Ontology, document)
        self.ontology = DetailClientMixin('ontologies', helpers.Ontology)
        self.terms = ListClientMixin('terms', helpers.Term, document)
        self.term = DetailClientMixin('terms', helpers.Term)
        self.search = SearchClientMixin('search', helpers.Term, document)
        self.detail = self.DetailClient()


if __name__ == "__main__":
    # TODO add arg parse and associated method calls
    print('Coming soon')
