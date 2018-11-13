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
import unittest
import warnings

import ebi.ols.api.helpers as helpers
from ebi.ols.api.client import OlsClient
import ebi.ols.api.exceptions

logging.basicConfig(level=logging.INFO,
                    format='%(asctime)s %(levelname)s : %(name)s.%(funcName)s(%(lineno)d) - %(message)s',
                    datefmt='%m-%d %H:%M:%S')

logger = logging.getLogger(__name__)


def ignore_warnings(test_func):
    def do_test(self, *args, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)
            test_func(self, *args, **kwargs)

    return do_test


class OntologyTestSuite(unittest.TestCase):
    """Basic test cases."""

    def _checkOntology(self, ontology):
        self.assertIsInstance(ontology, helpers.Ontology)
        self.assertIsInstance(ontology.config, helpers.OntologyConfig)
        self.assertIsInstance(ontology.config.annotations, helpers.OntologyAnnotation)

    def _checkProperty(self, property):
        self.assertIsInstance(property, helpers.Property)

    def _checkProperties(self, properties):
        [self._checkProperty(property) for property in properties]

    def _checkIndividual(self, individual):
        self.assertIsInstance(individual, helpers.Individual)

    def _checkIndividuals(self, individuals):
        [self._checkIndividual(ind) for ind in individuals]

    def _checkOntologies(self, ontologies):
        [self._checkOntology(ontology) for ontology in ontologies]

    def _checkMixed(self, helper):
        return getattr(self, '_check' + helper.__class__.__name__)(helper)

    @ignore_warnings
    def setUp(self):
        warnings.simplefilter("ignore", ResourceWarning)
        self.client = OlsClient(page_size=100)

    @ignore_warnings
    def test_ontologies_list(self):
        # standard first page
        ontologies = self.client.ontologies()
        self.assertEqual(ontologies.page_size, self.client.page_size)
        total_pages = ontologies.pages
        current = 0
        num_pages = 0
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
        self.assertEqual(ontologies.page, len(ontologies) // ontologies.page_size - 1)
        self.assertEqual(total_pages, num_pages)
        self.assertEqual(current, len(ontologies))
        self.assertEqual(num_pages, ontologies.pages)

    @ignore_warnings
    def test_ontology(self):
        # FIXME add further testing on single ontology data
        ontology = self.client.ontology('aero')
        self._checkOntology(ontology)

    def _checkTerm(self, term):
        self.assertIsInstance(term, helpers.Term)
        self.assertTrue(hasattr(term, 'iri'))
        self.assertTrue(hasattr(term, 'obo_xref'))

    def _checkTerms(self, terms):
        [self._checkTerm(term) for term in terms]

    @ignore_warnings
    def test_ontology_terms(self):
        """
        Tess retrieve ontology terms
        :return:
        """
        # Search for all terms in ontology, loop over and load Termn accordingly
        ontology = self.client.ontology("aero")
        terms = ontology.terms()
        self.assertEqual(terms.index, 0)
        self.assertGreaterEqual(len(terms), ontology.number_of_terms)
        self._checkTerms(terms)

    @ignore_warnings
    def test_ontology_individuals(self):
        ontology = self.client.ontology("aero")
        individuals = ontology.individuals()
        self.assertGreaterEqual(len(individuals), ontology.number_of_individuals)
        self._checkIndividuals(individuals)

    @ignore_warnings
    def test_ontology_properties(self):
        ontology = self.client.ontology("aero")
        properties = ontology.properties()
        self.assertGreaterEqual(len(properties), ontology.number_of_properties)
        self._checkProperties(properties)

    @ignore_warnings
    def test_list_range(self):
        ontology = self.client.ontology("aero")
        terms = ontology.terms({'size': self.client.page_size})

        slice_terms = terms[23:253]
        term_3 = terms[252]

        self.assertEqual(230, len(slice_terms))
        self.assertGreaterEqual(454, len(terms))
        current = 23
        for term in slice_terms:
            self.assertEqual(term.accession, terms[current].accession)
            current += 1
        self.assertEqual(slice_terms[len(slice_terms) - 1], term_3)

    @ignore_warnings
    def test_filters(self):
        """
        Test ontology terms api filtering options
        :return:
        """
        filters = {'short_form': 'EFO_0000405'}
        ontology = self.client.ontology('efo')
        ontologies = self.client.ontologies(filters={'fake_filter': 'fake_value'})

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

    @ignore_warnings
    def test_terms(self):
        """
        Test direct calls to terms entry point.
        Should warn that test may be long according to the nnumber of terms involved
        :return:
        """
        term_1 = helpers.Term(ontology_name='cco', iri='http://semanticscience.org/resource/SIO_010043')
        ancestors = term_1.load_relation('ancestors')
        for ancestor in ancestors:
            self._checkTerm(ancestor)
        self._checkTerm(term_1)


    @ignore_warnings
    def test_dynamic_links(self):
        term = helpers.Term(ontology_name='so', iri='http://purl.obolibrary.org/obo/SO_0000104')
        for relation in term.relations_types:
            related = term.load_relation(relation)
            if related:
                self._checkTerms(related)
        self.assertIn('derives_from', term.relations_types)
        term = helpers.Term(ontology_name='efo', iri='http://www.ebi.ac.uk/efo/EFO_0004799')
        self.assertIn('has_disease_location', term.relations_types)

    @ignore_warnings
    def test_search(self):
        """
        Need more tests for filtering and selected fields in Results
        :return:
        """
        # test search engine for terms
        results = self.client.search(query='gene_ontology')
        self.assertGreaterEqual(len(results), 15)
        i = 0
        for term in results:
            if i == 14:
                term_2 = term
                term_3 = self.client.detail(term)
                self._checkMixed(term_3)
            i += 1

        self._checkTerms(results)
        term_1 = results[14]
        self.assertEqual(term_2, term_1)
        # Test search which returns only properties
        properties = self.client.search(query='goslim_chembl')
        for prop in properties:
            self._checkMixed(prop)
            detailed = self.client.detail(prop)
            self._checkMixed(detailed)

        # Mixed helpers and slice on search
        mixed = self.client.search(query='go')
        i = 0
        clazz = []
        for mix in mixed:
            if i > 25:
                break
            clazz.append(mix.__class__.__name__) if mix.__class__.__name__ not in clazz else None
        self.assertGreater(len(clazz), 1)

    @ignore_warnings
    def test_individuals(self):
        self.assertTrue(True)
        ontology = self.client.ontology('aero')
        individuals = ontology.individuals()
        self._checkIndividuals(individuals)
        stop = 0
        for indi in individuals:
            if stop > 500:
                break
            stop += 1
            # print(stop, indi)

    @ignore_warnings
    def test_reverse_range(self):
        ontologies = self.client.ontologies()
        sliced = ontologies[158:110]
        self.assertEqual(len(sliced), 48)
        i = 158
        for ontology in sliced:
            self.assertEqual(ontology.ontology_id, ontologies[i].ontology_id)
            i -= 1

        sliced = ontologies[185:210]
        self.assertEqual(len(sliced), 25)
        i = 185
        for ontology in sliced:
            self.assertEqual(ontology.ontology_id, ontologies[i].ontology_id)
            i += 1

    def testErrorSearch(self):
        properties = self.client.search(query='goslim_yeast', filters={'ontology': 'go', 'type': 'property'})
        print(properties)

    def testAccession(self):
        accessions = ['TopObjectProperty', 'gocheck_do_not_annotate', 'SubsetProperty']
        for accession in accessions:
            o_term = helpers.Term(ontology_name='fake', short_form=accession)
            self.assertFalse(o_term.accession)

    def testException(self):
        # unknown URI
        with self.assertRaises(ebi.ols.api.exceptions.NotFoundException):
            h_term = helpers.Term(ontology_name='so', iri='http://purl.obolibrary.org/obo/SO_99999999')
            self.client.detail(h_term)
        with self.assertRaises(ebi.ols.api.exceptions.BadParameter):
            filters = {'accession': 'EFO:0000405'}
            terms = self.client.terms(filters=filters)

        with self.assertRaises(ebi.ols.api.exceptions.ServerError):
            prop = helpers.Property(iri='http://purl.obolibrary.org/obo/uberon/insect-anatomy#efo_slim',
                                    ontology_name='efo')
            terms = self.client.detail(prop)
        prop = helpers.Property(iri='http://purl.obolibrary.org/obo/uberon/insect-anatomy#efo_slim',
                                ontology_name='efo')
        terms = self.client.detail(prop)
