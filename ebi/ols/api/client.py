# -*- coding: utf-8 -*-
import time
import urllib.parse
import warnings

import coreapi.exceptions
from coreapi import Client, Document
from hal_codec import HALCodec

import ebi.ols.api.helpers as helpers
from ebi.ols.api.utils import has_next, has_first, has_last, has_prev


class OLSClient(object):
    """
    TODO: add individuals and properties services
    OLS Client ontologies client

    """
    base_url = "https://www.ebi.ac.uk/ols/api"
    decoders = [HALCodec()]
    base_document = None

    def __init__(self, url=None) -> None:
        self.client = Client(decoders=self.decoders)
        if url is not None:
            self.base_url = url
        self.base_document = self.client.get(self.base_url, force_codec=HALCodec)

    def ontologies(self, page=None, size=None) -> Document:
        params = {'page': page if page else '', 'size': size if size else 20}
        ontologies = self.client.action(self.base_document, ["ontologies"], params=params, validate=False)
        if 'ontologies' in ontologies.data:
            # only return ontologies if some exists
            return ontologies
        else:
            # else return a error
            raise coreapi.exceptions.ErrorMessage(
                helpers.Error(error="Bad Request", message="No corresponding ontologies", status=400,
                              path='ontologies', timestamp=time.time()))

    def ontology(self, onto_name) -> Document:
        """
        Get ontology details from its short identifier i.e go, fypo etc.

        :param onto_name:
        """
        uri = "/".join([self.base_url, "ontologies", onto_name])
        document = self.client.get(uri)
        return document

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
            path = self.base_url + '/terms'
            terms = self.client.action(self.base_document, ["terms"], params=params, validate=False)
        else:
            # update with eventual filters to apply
            # TODO add filters checks
            path = self.base_url + '/ontology/' + ontology_id + '/terms'
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
            '/'.join([self.base_url, 'ontologies', ontology_id, 'terms', encoded_iri]), force_codec=HALCodec)
        return document

    def search(self, filters=None) -> Document or coreapi.exceptions.ErrorMessage:
        # TODO take care of when search will be listed as method in base_uri

        if filters is None:
            filters = {}
        return None

    def next(self, document: Document) -> Document:
        if has_next(document):
            return self.client.action(document, ['next'])
        raise coreapi.exceptions.ErrorMessage(
            helpers.Error(error="Bad Request", message="No next item", status=400,
                          path='ontologies', timestamp=time.time()))

    def prev(self, document: Document) -> Document:
        if has_prev(document):
            return self.client.action(document, ['prev'])
        raise coreapi.exceptions.ErrorMessage(
            helpers.Error(error="Bad Request", message="No prev item", status=400,
                          path='ontologies', timestamp=time.time()))

    def last(self, document: Document) -> Document:
        if has_last(document):
            return self.client.action(document, ['last'])
        raise coreapi.exceptions.ErrorMessage(
            helpers.Error(error="Bad Request", message="No last item", status=400,
                          path='ontologies', timestamp=time.time()))

    def first(self, document: Document) -> Document:
        if has_first(document):
            return self.client.action(document, ['first'])
        raise coreapi.exceptions.ErrorMessage(
            helpers.Error(error="Bad Request", message="No first item", status=400,
                          path='ontologies', timestamp=time.time()))


class TermClient(OLSClient):

    def __init__(self, url: str = None, term: helpers.Term = None) -> None:
        encoded_iri = urllib.parse.quote_plus(urllib.parse.quote_plus(term.iri))
        base_url = super().base_url if url is None else url
        base_url += '/'.join(['/ontologies', term.ontology_name, 'terms', encoded_iri])
        super().__init__(base_url)

    def ancestors(self):
        return self.client.action(self.base_document, ['ancestors'])

    def parents(self, term):
        return self.client.action(self.base_document, ['parents'])

    def hierarchicalParents(self):
        return self.client.action(self.base_document, ['hierarchicalParents'])

    def hierarchicalAncestors(self):
        return self.client.action(self.base_document, ['hierarchicalAncestors'])

    def graphs(self):
        return self.client.action(self.base_url, ['graph'])

    def jstree(self):
        return self.client.action(self.base_url, ['jstree'])


if __name__ == "__main__":
    # TODO add arg parse and associated method calls
    print('Coming soon')
