# -*- coding: utf-8 -*-
import time
import urllib.parse
import warnings

import coreapi.exceptions
from coreapi import Client, Document
from hal_codec import HALCodec

import ebi.ols.api.helpers as helpers
import ebi.ols.api.exceptions as exceptions
import ebi.ols.api.utils as utils


class OlsRootClient(object):
    """
    TODO: add individuals and properties services
    OLS Client ontologies client

    """
    base_uri = "/ols/api"
    base_site = 'https://wwwdev.ebi.ac.uk'
    decoders = [HALCodec()]
    document = None

    @property
    def uri(self):
        return self.base_site + self.base_uri

    class OntologiesClient(object):
        base_uri = "/ols/api/ontologies"
        current = None

        def __init__(self, client) -> None:
            super().__init__()
            self.client = client.client
            self.current = client.document

        def list(self, page=None, size=None) -> [helpers.Ontology] or exceptions.BadParameter:
            params = {'page': page if page else '', 'size': size if size else 20}
            self.current = self.client.action(self.current, ['ontologies'], params=params, validate=False)

            if 'ontologies' in self.current.data:
                # only return ontologies if some exists
                return utils.OntologyList(self.client, self.current)
            else:
                # else return a error
                raise exceptions.NotFoundException(
                    helpers.Error(error="Not Found", message="No corresponding ontologies for request",
                                  status=404, path='ontologies', timestamp=time.time()))

        def _load(self, ontology_id):
            document = self.client.get('/'.join([self.uri, ontology_id]))
            return document

        def details(self, ontology_id):
            return self._load(ontology_id)

        def terms(self, page=None, size=None):
            if not self.document:
                document = self._load()
            terms = self.client.action(document, ['terms'])
            if 'terms' in terms.data:
                return document
            else:
                raise exceptions.NotFoundException(
                    helpers.Error(error="Not Found", message="No corresponding terms for request",
                                  status=404, path='ontologies', timestamp=time.time()))

    class IndividualsClient():
        def __init__(self, document) -> None:
            super().__init__()
            self.document = document

    class PropertiesClient():
        def __init__(self, document) -> None:
            super().__init__()
            self.document = document

    class TermsClient():
        def __init__(self, document) -> None:
            super().__init__()
            self.document = document

        def details(self, ontology, iri):
            encoded_iri = urllib.parse.quote_plus(urllib.parse.quote_plus(iri))
            base_url = super().base_uri + '/'.join(['/ontologies', ontology, 'terms', encoded_iri])
            return self.document.load(base_url)


        def ancestors(self):
            return self.client.action(self.document, ['ancestors'])

        def parents(self, term):
            return self.client.action(self.document, ['parents'])

        def hierarchicalParents(self):
            return self.client.action(self.document, ['hierarchicalParents'])

        def hierarchicalAncestors(self):
            return self.client.action(self.document, ['hierarchicalAncestors'])

        def graphs(self):
            return self.client.action(self.base_uri, ['graph'])

        def jstree(self):
            return self.client.action(self.base_uri, ['jstree'])

    def __init__(self) -> None:
        super().__init__()
        self.client = Client(decoders=self.decoders)
        self.document = self.client.get(self.uri, force_codec=HALCodec)
        self.ontologies = self.OntologiesClient(self)
        # self.terms = self.TermsClient(self)
        # self.individuals = self.IndividualsClient(self)
        # self.properties = self.PropertiesClient(self)

    """
    def ontologies(self, page=None, size=None) -> Document:
        params = {'page': page if page else '', 'size': size if size else 20}
        ontologies = self.client.action(self.document, ["ontologies"], params=params, validate=False)
        if 'ontologies' in ontologies.data:
            # only return ontologies if some exists
            return ols.api.utils.load_ontologies(ontologies, self)
        else:
            # else return a error
            raise exceptions.NotFoundException(
                helpers.Error(error="Not Found", message="No corresponding ontologies for request",
                              status=404, path='ontologies', timestamp=time.time()))
    """

    def ontology(self, ontology_id) -> OntologiesClient:
        """
        Short cut method to load an return a single Ontology document via a OntologyClient.details
        :param: ontology_id the ontology unique id

        """
        return self.OntologyClient(ontology_id)

    def terms(self, ontology_id, page=None, size=None, filters=None) -> Document or coreapi.exceptions.ErrorMessage:
        """
        Get ontologies terms, if no filter set, return a first page of terms
        TODO more testing about terms filtering parameters currently available in API
        :param ontology_id: ontology unique short code
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
        if ontology_id is None:
            # direct terms list
            if params.get('size') < 200:
                warnings.warn('You should not consider calling terms without higher page size, request may be slow')
                params['size'] = 200
            path = self.base_uri + '/terms'
            terms = self.client.action(self.document, ["terms"], params=params, validate=False)
        else:
            # update with eventual filters to apply
            # TODO add filters checks
            path = self.base_uri + '/ontology/' + ontology_id + '/terms'
            try:
                assert set(filters.keys()).issubset({'iri', 'obo_id', 'short_form'}), "Unauthorized filter key"
                assert len(filters.keys()) <= 1, "Only one filter can be applied at a time"
            except AssertionError as e:
                raise coreapi.exceptions.ErrorMessage(
                    helpers.Error(error="Bad Request", message=str(e), status=400,
                                  path=path, timestamp=time.time()))
            params.update(filters)
            document = self.ontology(ontology_id)
            terms = self.client.action(document, ['terms'], params=params, validate=False)

        if 'terms' in terms.data:
            # only return ontologies if some exists
            return terms
        else:
            # else return a error
            raise coreapi.exceptions.ErrorMessage(
                helpers.Error(error="Bad Request", message="No corresponding terms", status=400,
                              path=path, timestamp=time.time()))

    def term(self, ontology_id, term_iri) -> Document or coreapi.exceptions.ErrorMessage:
        encoded_iri = urllib.parse.quote_plus(urllib.parse.quote_plus(term_iri))
        document = self.client.get(
            '/'.join([self.base_uri, 'ontologies', ontology_id, 'terms', encoded_iri]), force_codec=HALCodec)
        return document

    def search(self, filters=None) -> Document or coreapi.exceptions.ErrorMessage:
        # TODO take care of when search will be listed as method in base_uri

        if filters is None:
            filters = {}
        return None




if __name__ == "__main__":
    # TODO add arg parse and associated method calls
    print('Coming soon')
