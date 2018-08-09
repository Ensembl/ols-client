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

        def __call__(self, item, **kwargs):
            if isinstance(item, helpers.Property):
                client = DetailClientMixin('ontologies/{}/properties'.format(item.ontology_name), helpers.Property)
                return client(item.iri)
            elif isinstance(item, helpers.Individual):
                client = DetailClientMixin('ontologies/{}/individuals'.format(item.ontology_name), helpers.Ontology)
            elif isinstance(item, helpers.Ontology):
                client = DetailClientMixin('ontologies', helpers.Ontology)
            elif isinstance(item, helpers.Term):
                client = DetailClientMixin('ontologies/{}/terms'.format(item.ontology_name), helpers.Term)
            else:
                assert('ontology_name' in kwargs)
                assert('iri' in kwargs)
                assert(issubclass(item, helpers.OLSHelper))
                inst = item(ontology_name=kwargs.get('ontology_name'), iri=kwargs.get('iri'))
                return self.__call__(inst)
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
