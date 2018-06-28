# -*- coding: utf-8 -*-
import time
import urllib.parse
import warnings

import coreapi.exceptions
from coreapi import Client, Document
from hal_codec import HALCodec

import ebi.ols.api.exceptions as exceptions
import ebi.ols.api.utils as utils
import ebi.ols.api.helpers as helpers
import ebi.ols.api.lists as lists


class OntologiesClient(object):
    urn = "/ols/api/ontologies"
    document = None

    @property
    def uri(self):
        return self.parent.site + self.urn

    def __init__(self, parent) -> None:
        self.parent = parent
        self.document = parent.document

    def list(self, page=None, size=None) -> [helpers.Ontology] or exceptions.BadParameter:
        params = {'page': page if page else '', 'size': size if size else 20}
        document = self.parent.client.action(self.document, ['ontologies'], params=params, validate=False)

        if 'ontologies' in document.data:
            # only return ontologies if some exists
            return lists.OntologyList(self.parent, document)
        else:
            # else return a error
            raise exceptions.BadParameter(
                helpers.Error(error="Bad Parameter", message="No corresponding ontologies for request",
                              status=400, path='ontologies', timestamp=time.time()))

    def details(self, ontology_id):
        try:
            document = self.parent.client.get('/'.join([self.uri, ontology_id]))
            return utils.load_ontology(document)
        except coreapi.exceptions.CoreAPIException as e:
            raise exceptions.OlsException(e)


class IndividualsClient(object):
    def __init__(self, document) -> None:
        super().__init__()
        self.document = document


class PropertiesClient(object):
    def __init__(self, document) -> None:
        super().__init__()
        self.document = document


class TermsClient(object):
    urn = "/ols/api/terms"

    def uri(self, ontology=None):
        if ontology:
            return '/'.join([OlsClient.site, OntologiesClient.urn, ontology])
        return OlsClient.site + self.urn

    def __init__(self, client) -> None:
        self.client = client.client
        self.document = client.document

    def list(self, ontology=None, page=None, size=None, filters=None) -> lists.TermList:
        """
        Get ontologies terms, if no filter set, return a first page of terms
        TODO more testing about terms filtering parameters currently available in API
        :param ontology: ontology unique short code
        :param size: size of excpeted list, default 20
        :param page: the requested page number
        :param filters: a dict with following possible keys
            - type: Restrict a search to an entity type, one of {class,property,individual,ontology}
            - slim: Restrict a search to an particular set of slims by name
            - fieldList: Specify the fields to return, the defaults are {iri,label,short_form,obo_id,ontology_name,ontology_prefix,description,type}
            - obsoletes: Set to true to include obsoleted terms in the results
            - local: Set to true to only return terms that are in a defining ontology e.g. Only return matches to gene ontology terms in the gene ontology, and exclude ontologies where those terms are also referenced
            - childrenOf: You can restrict a search to all children of a given term. Supply a list of IRI for the terms that you want to search under (subclassOf/is-a relation only)
            - allChildrenOf: You can restrict a search to all children of a given term. Supply a list of IRI for the terms that you want to search under (subclassOf/is-a plus any hierarchical/transitive properties like 'part of' or 'develops from')
            - rows: How many results per page
            - start: The results page number
        :return: A list of Term
        """
        if filters is None:
            filters = {}
        params = {'page': page if page else '', 'size': size if size else 20}
        if ontology:
            path = self.uri(ontology)
            document = self.client.get(path)
        else:
            warnings.warn('You should not consider calling terms without ontology filter, request may be slow')
            if params.get('size') < 200:
                params['size'] = 200
            path = self.uri()
            document = self.document
        try:
            assert set(filters.keys()).issubset({'iri', 'obo_id', 'short_form'}), "Unauthorized filter key"
            assert len(filters.keys()) <= 1, "Only one filter can be applied at a time"
            params.update(filters)
        except AssertionError as e:
            raise exceptions.BadParameter(helpers.Error(error="Bad Request", message=str(e), status=400,
                                                        path=path, timestamp=time.time()))
        terms = self.client.action(document, ['terms'], params=params, validate=False)

        if 'terms' in terms.data:
            # only return ontologies if some exists
            return lists.TermList(self, terms)
        else:
            # else return a error
            raise exceptions.BadParameter(
                helpers.Error(error="Bad Parameter", message="No corresponding terms for request",
                              status=400, path='terms', timestamp=time.time()))

    def details(self, ontology, iri):
        encoded_iri = urllib.parse.quote_plus(urllib.parse.quote_plus(iri))
        base_url = '/'.join([self.uri(ontology), 'terms', encoded_iri])
        self.document = self.client.get(base_url)
        return utils.load_term(self.client.get(base_url))

    def ancestors(self, term):
        ancestors = self.client.action(self.document, ['ancestors'])
        return lists.TermList(self, ancestors)

    def parents(self, term):
        return self.client.action(self.document, ['parents'])

    def hierarchicalParents(self):
        return self.client.action(self.document, ['hierarchicalParents'])

    def hierarchicalAncestors(self):
        return self.client.action(self.document, ['hierarchicalAncestors'])

    def graphs(self):
        return self.client.action(self.document, ['graph'])

    def jstree(self):
        return self.client.action(self.document, ['jstree'])


class OlsClient(object):
    """
    TODO: add individuals and properties services
    OLS Client ontologies client

    """
    site = 'https://www.ebi.ac.uk'
    uri = "/ols/api"
    decoders = [HALCodec()]
    document = None

    @property
    def url(self):
        return self.site + self.uri

    def __init__(self, site=None) -> None:
        self.client = Client(decoders=self.decoders)
        if site:
            self.site = site
        self.document = self.client.get(self.url, force_codec=HALCodec)
        self.ontologies = OntologiesClient(self)
        self.terms = TermsClient(self)
        self.individuals = IndividualsClient(self)
        self.properties = PropertiesClient(self)

    def ontology(self, ontology_id) -> helpers.Ontology:
        """
        Short cut method to load an return a single Ontology document via a OntologyClient.details
        :param: ontology_id the ontology unique id

        """
        return self.ontologies.details(ontology_id)

    def term(self, ontology, iri):
        return self.terms.details(ontology, iri)

    def search(self, filters=None) -> Document or coreapi.exceptions.ErrorMessage:
        # TODO take care of when search will be listed as method in base_uri

        if filters is None:
            filters = {}
        return None


if __name__ == "__main__":
    # TODO add arg parse and associated method calls
    print('Coming soon')
