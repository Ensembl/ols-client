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

import ebi.ols.api.exceptions
import ebi.ols.api.exceptions as exceptions
import ebi.ols.api.helpers as helpers
from ebi.ols.api.client import OlsClient

logging.basicConfig(level=logging.DEBUG,
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

    def _checkProperty(self, prop):
        self.assertIsInstance(prop, helpers.Property)

    def _checkProperties(self, properties):
        if type(properties) is helpers.Property:
            properties = [properties]
        [self._checkProperty(prop) for prop in properties]

    def _checkIndividual(self, individual):
        self.assertIsInstance(individual, helpers.Individual)

    def _checkIndividuals(self, individuals):
        [self._checkIndividual(ind) for ind in individuals]

    def _checkOntologies(self, ontologies):
        [self._checkOntology(ontology) for ontology in ontologies]

    def _checkMixed(self, helper):
        return getattr(self, '_check' + helper.__class__.__name__)(helper)

    def setUp(self):
        warnings.simplefilter("ignore", ResourceWarning)
        self.client = OlsClient(page_size=100)

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

    def test_ontology_individuals(self):
        ontology = self.client.ontology("aero")
        individuals = ontology.individuals()
        self.assertGreaterEqual(len(individuals), ontology.number_of_individuals)
        self._checkIndividuals(individuals)

    def test_ontology_properties(self):
        ontology = self.client.ontology("aero")
        properties = ontology.properties()
        self.assertGreaterEqual(len(properties), ontology.number_of_properties)
        self._checkProperties(properties)

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
        with self.assertRaises(KeyError):
            error_slice = terms[1:550]
        with self.assertRaises(IndexError):
            current = slice_terms[12555]
        with self.assertRaises(TypeError):
            current = slice_terms['12512']

    def test_list_filters(self):
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

    def test_dynamic_links(self):
        term = helpers.Term(ontology_name='so', iri='http://purl.obolibrary.org/obo/SO_0000104')
        for relation in term.relations_types:
            related = term.load_relation(relation)
            if related:
                self._checkTerms(related)
        self.assertIn('derives_from', term.relations_types)
        term = helpers.Term(ontology_name='efo', iri='http://www.ebi.ac.uk/efo/EFO_0004799')
        self.assertIn('has_disease_location', term.relations_types)

    def test_search_simple(self):
        """
        Test Basic, simple query param
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

    def test_search_filters(self):
        """
        Test Search feature :
        - with dictionary parameter
        - kwargs passed
        """
        # Test search which returns only properties
        properties = self.client.search(query='goslim_chembl', filters={'type': 'property'})
        for prop in properties:
            self._checkMixed(prop)
            detailed = self.client.detail(prop)
            self._checkMixed(detailed)

    def test_search_kwargs(self):
        """
        Test Search feature : - kwargs passed
        """
        mixed = self.client.search(query='go', type='property')
        self.assertGreaterEqual(len(mixed), 500)

        clazz = []
        for mix in mixed:
            clazz.append(mix.__class__.__name__) if mix.__class__.__name__ not in clazz else None
        self.assertEqual(len(clazz), 1)
        clazz = []
        # only terms and properties
        mixed = self.client.search(query='go', ontology='efo')
        self.assertGreater(len(mixed), 1)
        for mix in mixed:
            clazz.append(mix.__class__.__name__) if mix.__class__.__name__ not in clazz else None
        self.assertEqual(len(clazz), 2)
        # test obsoletes
        mixed = self.client.search(query='GO_0003698', ontology='go', obsoletes='true', type='term')
        found_obsolete = False
        for mix in mixed:
            detailed = self.client.detail(ontology_name='go', iri=mix.iri, type=helpers.Term)
            found_obsolete = found_obsolete or (detailed.is_obsolete == 1)
        self.assertTrue(found_obsolete)

        mixed = self.client.search(query='go', ontology='efo', fieldList='iri,label,short_form,obo_id')
        self.assertGreater(len(mixed), 0)
        mixed = self.client.search(query='goslim_metagenomics', type='property',
                                   queryFields='label,logical_description,iri')
        self.assertGreater(len(mixed), 0)
        mixed = self.client.search(query='go', ontology='efo', fieldList={'iri', 'label', 'short_form', 'obo_id'})
        self.assertGreater(len(mixed), 0)
        print('nb pages ', mixed.pages)
        for mix in mixed:
            if mixed.page > 2:
                break
            self._checkMixed(mix)
        mixed = self.client.search(query='goslim_metagenomics', ontology='go', type='property',
                                   queryFields={'label', 'logical_description', 'iri'})
        self.assertGreater(len(mixed), 0)

    def test_search_wrong_filters(self):
        with self.assertRaises(exceptions.BadFilters) as ex:
            self.client.search(query='go', type='property,unknown', ontology='efo')
            self.assertIn('type', ex.message)
        with self.assertRaises(exceptions.BadFilters) as ex:
            self.client.search(query='go', type='property,term', ontology='efo', obsoletes='totototo')
            self.assertIn('obsoletes', ex.message)
        with self.assertRaises(exceptions.BadFilters) as ex:
            self.client.search(query='go', ontology='efo', local='1')
            self.assertIn('local', ex.message)
        with self.assertRaises(exceptions.BadFilters) as ex:
            self.client.search(query='go', ontology='efo', fieldList={'iri', 'label', 'wrong_short_form', 'obo_id'})
            self.assertIn('fieldList', ex.message)
        with self.assertRaises(exceptions.BadFilters) as ex:
            self.client.search(query='go', ontology='efo', queryFields={'label', 'logical_description_wrong', 'iri'})
            self.assertIn('queryFields', ex.message)

    def test_individuals(self):
        ontology = self.client.ontology('aero')
        individuals = ontology.individuals()
        self._checkIndividuals(individuals)

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

    def test_error_search(self):
        properties = self.client.search(query='goslim_yeast', filters={'ontology': 'go', 'type': 'property'})
        for prop in properties:
            details = self.client.detail(ontology_name='go', iri=prop.iri, type=helpers.Property)
            print(details)

    def test_accessions(self):
        accessions = ['TopObjectProperty', 'SubsetProperty', 'ObsoleteClass']
        for accession in accessions:
            prop = helpers.Property(short_form=accession)
            self.assertIsNone(prop.accession)
        iris = ['http://purl.obolibrary.org/obo/go#gocheck_do_not_annotate']
        for accession in iris:
            prop = helpers.Property(iri=accession)
            self.assertIsNotNone(prop.accession)
            o_property = self.client.property(accession, unique=False)
            self.assertIsNotNone(o_property)
            self._checkProperties(o_property)

    def test_exception_retry(self):
        # unknown URI
        with self.assertRaises(ebi.ols.api.exceptions.NotFoundException):
            h_term = helpers.Term(ontology_name='so', iri='http://purl.obolibrary.org/obo/SO_99999999')
            self.client.detail(h_term)
        with self.assertRaises(ebi.ols.api.exceptions.NotFoundException):
            self.client.ontology('unexisting_ontology')
        with self.assertRaises(ebi.ols.api.exceptions.BadFilters):
            filters = {'accession': 'EFO:0000405'}
            self.client.terms(filters=filters)
        with self.assertRaises(ebi.ols.api.exceptions.ObjectNotRetrievedError):
            prop = helpers.Property(iri='http://purl.obolibrary.org/obo/uberon/insect-anatomy#efo_slim',
                                    ontology_name='efo')
            self.client.detail(prop)

    def test_namespace(self):
        # retrieved from namespace annotation
        h_term = helpers.Term(ontology_name='phi', iri='http://purl.obolibrary.org/obo/PHI_2000021')
        self.client.detail(h_term)
        self.assertIsNotNone(h_term.namespace)

        # retrieved from obo_name_space annotation
        h_term = helpers.Term(ontology_name='go', iri='http://purl.obolibrary.org/obo/GO_0005230')
        self.client.detail(h_term)
        self.assertIsNotNone(h_term.namespace)

    def test_overwritten_site(self):
        overriden_site = 'https://wwwdev.ebi.ac.uk/ols/api'
        self.client = OlsClient(base_site=overriden_site)
        ontology = self.client.ontology('phi')
        self.assertTrue(self.client.ontology.uri.startswith(overriden_site))
        terms = ontology.terms()
        self.assertTrue(terms.uri.startswith(overriden_site))
