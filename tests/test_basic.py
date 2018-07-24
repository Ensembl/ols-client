# -*- coding: utf-8 -*-

import unittest

import ebi.ols.api.exceptions as exceptions
import ebi.ols.api.helpers as helpers
import ebi.ols.api.lists as lists
from ebi.ols.api.client import OlsClient


class OntologyTestSuite(unittest.TestCase):
    """Basic test cases."""

    def _checkOntology(self, ontology):
        self.assertIsInstance(ontology, helpers.Ontology)
        self.assertIsInstance(ontology.config, helpers.Config)
        self.assertIsInstance(ontology.config.annotations, helpers.OntoAnnotation)

    def _checkProperty(self, property):
        self.assertIsInstance(property, helpers.Property)

    def _checkProperties(self, properties):
        self.assertEqual(properties.page_size, 100)
        [self._checkProperty(property) for property in properties]

    def _checkIndividual(self, individual):
        self.assertIsInstance(individual, helpers.Individual)

    def _checkIndividuals(self, individuals):
        self.assertEqual(individuals.page_size, 100)
        [self._checkIndividual(ind) for ind in individuals]

    def _checkOntologies(self, ontologies):
        self.assertEqual(ontologies.page_size, 100)
        [self._checkOntology(ontology) for ontology in ontologies]

    def setUp(self):
        super().setUp()
        self.client = OlsClient()

    def test_ontologies_list(self):
        # standard first page
        ontologies = self.client.ontologies()
        self.assertEqual(ontologies.page_size, 100)
        total_pages = ontologies.pages
        current = 0
        num_pages = 1
        test_item = None
        for ontology in ontologies:
            if current == 185:
                test_item = ontology
            self._checkOntology(ontology)
            current = current + 1
            if current % ontologies.page_size == 0:
                num_pages += 1
        item = ontologies[185]
        self.assertEqual(test_item, item)
        self.assertEqual(ontologies.index, 85)
        self.assertEqual(ontologies.page, 1)
        self.assertEqual(total_pages, num_pages)
        self.assertEqual(current, len(ontologies))
        self.assertEqual(num_pages, ontologies.pages)

    def test_ontology(self):
        ontology = self.client.ontology('aero')
        self._checkOntology(ontology)
        self._checkTerms(ontology.terms())
        individuals = ontology.individuals()
        self._checkIndividuals(individuals)
        properties = ontology.properties()
        self._checkProperties(properties)

    def test_failed_ontology(self):
        with self.assertRaises(exceptions.OlsException):
            self.client.ontology('non_existing_ontology')

    def _checkTerm(self, term):
        self.assertIsInstance(term, helpers.Term)
        self.assertTrue(hasattr(term, 'iri'))
        self.assertTrue(hasattr(term, 'obo_xref'))

    def _checkTerms(self, terms):
        self.assertEqual(terms.page_size, 100)
        [self._checkTerm(term) for term in terms]

    def test_ontology_terms(self):
        """
        Tess retrieve ontology terms
        :return:
        """
        # Search for all terms in ontology, loop over and load Termn accordingly
        ontology = self.client.ontology("co_337")
        terms = ontology.terms()
        self.assertEqual(terms.page_size, 100)
        self.assertEqual(terms.index, 0)
        self._checkTerms(terms)

    def test_ontology_terms_filters(self):
        """
        Test ontology terms api filtering options
        :return:
        """
        filters = {'short_form': 'EFO_0000405'}
        ontology = self.client.ontology('efo')
        terms = ontology.terms(filters=filters)
        for term in terms:
            self.assertEqual(term.short_form, 'EFO_0000405')
        filters = {'obo_id': 'EFO:0000405'}
        terms = ontology.terms(filters=filters)
        for term in terms:
            self.assertEqual(term.obo_id, 'EFO:0000405')

        filters = {'iri': 'http://www.ebi.ac.uk/efo/EFO_1000838'}
        terms = ontology.terms(filters=filters)
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
        terms = self.client.terms()
        self.assertGreater(len(terms), 100)
        print(terms.total)

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
        self._checkTerms(terms)

    def test_individuals(self):
        self.assertTrue(True)
