# -*- coding: utf-8 -*-

import unittest
import warnings
import coreapi.exceptions

import ebi.ols.api.helpers as helpers
import ebi.ols.api.utils as utils
import ols.api.utils
from ebi.ols.api.client import OlsRootClient


class OntologyTestSuite(unittest.TestCase):
    """Basic test cases."""
    def setUp(self):
        super().setUp()
        self.client = OlsRootClient()

    def test_ontologies_list(self):
        # standard first page
        ontologies = self.client.ontologies.list(size=50)
        # print(document)
        self.assertEqual(ontologies.size, 50)
        total_pages = ontologies.total_pages
        print('total pages', total_pages)
        current = 1
        while ontologies.has_next:
            # document = self.client.ontologies(page=current)
            ontologies = ontologies.next()
            current = current + 1
        self.assertEqual(total_pages, current)

    def test_ontology_client(self):
        onto = self.client.ontologies.details('fypo')
        ontology = ols.api.utils.load_ontology(onto)
        self._checkTerms(ontology, document)

    def _checkOntology(self, ontology, document):
        self.assertTrue('ontologyId' in document)
        self.assertEqual(ontology.ontologyId, document['ontologyId'])
        self.assertIsInstance(ontology, helpers.Ontology)
        self.assertIsInstance(ontology.config, helpers.Config)
        self.assertIsInstance(ontology.config.annotations, helpers.OntoAnnotation)

    def _checkOntologies(self, ontologies, ontology_list):
        i = 0
        for ontology in ontologies:
            self._checkOntology(ontology, ontology_list[i])
            i += 1
        return i

    def test_pagination_error(self):
        # change page size
        ontologies = self.client.ontologies()
        pages = ontologies.data['page']
        total_pages = pages['totalPages']
        # Pagination error
        with self.assertRaises(coreapi.exceptions.ErrorMessage):
            self.client.ontologies(page=total_pages + 10)

    def test_load_ontology(self):
        document = self.client.ontology('go')
        ontology = ols.api.utils.load_ontology(document)
        self._checkOntology(ontology, document)

    def test_failed_ontology(self):
        with self.assertRaises(coreapi.exceptions.ErrorMessage):
            self.client.ontology('non_existing_ontology')

    def _checkTerm(self, term, document):
        self.assertIsInstance(term, helpers.Term)
        self.assertEqual(term.iri, document.data['iri'])
        self.assertEqual(term.obo_xref, document.data['obo_xref'])

    def _checkTerms(self, terms, term_list):
        i = 0
        for term in terms:
            self._checkTerm(term, term_list[i])
            i += 1
        return i

    def test_ontology_terms(self):
        """
        Tess retrieve ontology terms
        :return:
        """
        # Search for all terms in ontology, loop over and load Termn accordingly
        document = self.client.terms("fypo")
        page = document.data['page']
        self.assertEqual(page['size'], 20)
        self.assertEqual(page['number'], 0)
        doc_terms = document.data['terms']
        terms = ols.api.utils.load_terms(document)
        count = self._checkTerms(terms, doc_terms)
        self.assertEqual(count, page['size'])

    def test_ontology_terms_filters(self):
        """
        Test ontology terms api filtering options
        :return:
        """
        filters = {'short_form': 'EFO_0000405'}
        document = self.client.terms('efo', filters=filters)
        terms = ols.api.utils.load_terms(document)
        for term in terms:
            self.assertEqual(term.short_form, 'EFO_0000405')

        filters = {'obo_id': 'EFO:0000405'}
        document = self.client.terms('efo', filters=filters)
        terms = ols.api.utils.load_terms(document)
        for term in terms:
            self.assertEqual(term.obo_id, 'EFO:0000405')

        filters = {'iri': 'http://www.ebi.ac.uk/efo/EFO_1000838'}
        document = self.client.terms('efo', filters=filters)
        terms = ols.api.utils.load_terms(document)
        for term in terms:
            self.assertEqual(term.short_form, 'EFO_1000838')
            self.assertEqual(term.obo_id, 'EFO:1000838')
            self.assertEqual(term.iri, 'http://www.ebi.ac.uk/efo/EFO_1000838')

    def test_terms(self):
        """
        Test direct calls to terms entry point.
        Should warn that test may be long according to the nnumber of terms involved
        :return:
        """
        with warnings.catch_warnings():
            document = self.client.terms(None)
            page = document.data['page']
            doc_terms = document.data['terms']
            terms = ols.api.utils.load_terms(document)
            self.assertGreater(len(terms), 0)
            count = self._checkTerms(terms, doc_terms)
            self.assertEquals(count, page['size'])

    def test_ontology_term(self):
        terms = ols.api.utils.load_terms(self.client.terms('lbo'))
        for term in terms:
            direct_term = self.client.term('lbo', term.iri)
            # direct_term = helpers.load_term(direct_term)
            self._checkTerm(term, direct_term)
            term_client = TermsClient(self.base_url, term)
            ancestors_doc = term_client.ancestors()
            ancestors = ols.api.utils.load_terms(ancestors_doc)
            self._checkTerms(ancestors, ancestors_doc.data['terms'])

    def test_search(self):
        # test search engine for terms
        pass

    def test_individuals(self):
        self.assertTrue(True)
