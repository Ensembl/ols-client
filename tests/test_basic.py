# -*- coding: utf-8 -*-

import unittest

import ebi.ols.api.exceptions as exceptions
import ebi.ols.api.helpers as helpers
import ebi.ols.api.lists as lists
from ebi.ols.api.client import OlsClient
from ebi.ols.api.exceptions import *


class OntologyTestSuite(unittest.TestCase):
    """Basic test cases."""
    def setUp(self):
        super().setUp()
        self.client = OlsClient('https://www.ebi.ac.uk')

    def test_ontologies_list(self):
        # standard first page
        ontologies = self.client.ontologies.list(size=50)
        self.assertEqual(ontologies.page_size, 50)
        total_pages = ontologies.nb_pages
        current = 1
        elms = ontologies.first_page()
        self._checkOntologies(elms)
        count = len(elms)
        while ontologies.has_next_page:
            # document = self.client.ontologies(page=current)
            elms = ontologies.next_page()
            self._checkOntologies(elms)
            current = current + 1
            count += len(elms)
        self.assertEqual(total_pages, current)
        self.assertEqual(count, ontologies.total)
        self.assertEqual(current, ontologies.nb_pages)
        # loop in reverse
        while ontologies.has_prev_page:
            ontologies.prev_page()
            current -= 1
        self.assertEqual(current, 1)

    def test_ontology(self):
        ontology = self.client.ontologies.details('co_337')
        self._checkOntology(ontology)
        terms = self.client.terms.list(ontology=ontology.ontologyId, size=100)
        self.assertEqual(terms.page_size, 100)
        self.assertGreater(terms.nb_pages, 3)
        # check only the five first pages
        for i in range(1, 4):
            terms = self.client.terms.list(ontology=ontology.ontologyId, page=i, size=100)
            self._checkTerms(terms.current_page())

    def _checkOntology(self, ontology):
        self.assertIsInstance(ontology, helpers.Ontology)
        self.assertIsInstance(ontology.config, helpers.Config)
        self.assertIsInstance(ontology.config.annotations, helpers.OntoAnnotation)

    def _checkOntologies(self, ontologies):
        [self._checkOntology(ontology) for ontology in ontologies]

    def test_pagination_error(self):
        # change page size
        ontologies = self.client.ontologies.list()
        pages = ontologies.nb_pages
        # Pagination error
        with self.assertRaises(BadParameter):
            self.client.ontologies.list(page=pages + 10)

    def test_failed_ontology(self):
        with self.assertRaises(exceptions.OlsException):
            self.client.ontology('non_existing_ontology')

    def _checkTerm(self, term):
        self.assertIsInstance(term, helpers.Term)
        self.assertTrue(hasattr(term, 'iri'))
        self.assertTrue(hasattr(term, 'obo_xref'))

    def _checkTerms(self, terms):
        return [self._checkTerm(term) for term in terms]

    def test_ontology_terms(self):
        """
        Tess retrieve ontology terms
        :return:
        """
        # Search for all terms in ontology, loop over and load Termn accordingly
        terms = self.client.terms.list("co_337")
        self.assertEqual(terms.page_size, 20)
        self.assertEqual(terms.current, 0)
        checked = self._checkTerms(terms)
        self.assertEqual(len(checked), len(terms))

    def test_ontology_terms_filters(self):
        """
        Test ontology terms api filtering options
        :return:
        """
        filters = {'short_form': 'EFO_0000405'}
        terms = self.client.terms.list('efo', filters=filters)
        for term in terms:
            self.assertEqual(term.short_form, 'EFO_0000405')

        filters = {'obo_id': 'EFO:0000405'}
        terms = self.client.terms.list('efo', filters=filters)
        for term in terms:
            self.assertEqual(term.obo_id, 'EFO:0000405')

        filters = {'iri': 'http://www.ebi.ac.uk/efo/EFO_1000838'}
        terms = self.client.terms.list('efo', filters=filters)
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
        with self.assertWarns(UserWarning):
            self.client.terms.list(None)

    def test_ontology_term(self):
        terms = self.client.terms.list('lbo')
        for term in terms.first_page():
            direct_term = self.client.term('lbo', term.iri)
            # direct_term = helpers.load_term(direct_term)
            self._checkTerm(term)
            self.assertEqual(term, direct_term)
            ancestors = self.client.terms.ancestors(direct_term)
            self.assertIsInstance(ancestors, lists.TermList)

    def test_search(self):
        """
        Need more tests for filtering and selected fields in Results
        :return:
        """
        # test search engine for terms
        terms = self.client.search(query='transcriptome', rows=50)
        self.assertGreaterEqual(terms.nb_pages, 3)
        for term in terms:
            print(term.label)

    def test_individuals(self):
        self.assertTrue(True)
