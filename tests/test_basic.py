# -*- coding: utf-8 -*-

import unittest
import warnings

import coreapi.exceptions

from ebi.ols.api.client import OLSClient
import ebi.ols.api.helpers as helpers


def ignore_warnings(test_func):
    def do_test(self, *args, **kwargs):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", ResourceWarning)
            test_func(self, *args, **kwargs)

    return do_test


class BasicTestSuite(unittest.TestCase):
    """Basic test cases."""

    def setUp(self):
        super().setUp()
        self.client = OLSClient("https://wwwdev.ebi.ac.uk/ols/api")

    @ignore_warnings
    def test_ontologies_list(self):
        # standard first page
        ontologies = self.client.ontologies()
        self.assertTrue('page' in ontologies)
        self.assertTrue('next' in ontologies)
        pages = ontologies.data['page']
        self.assertEqual(pages['size'], 20)
        self.assertEqual(pages['number'], 0)
        total_pages = pages['totalPages']
        current = 1
        while 'next' in ontologies:
            ontologies = self.client.ontologies(page=current)
            current = current + 1
        self.assertEqual(current, total_pages)

    @ignore_warnings
    def test_pagination_error(self):
        # change page size
        ontologies = self.client.ontologies()
        pages = ontologies.data['page']
        total_pages = pages['totalPages']
        # Pagination error
        with self.assertRaises(coreapi.exceptions.ErrorMessage):
            self.client.ontologies(page=total_pages + 10)

    @ignore_warnings
    def test_load_ontology(self):
        document = self.client.ontology('go')
        ontology = helpers.load_ontology(document)
        self.assertTrue('ontologyId' in document)
        self.assertEqual(ontology.ontologyId, document['ontologyId'])
        # TODO add inner objects test such as Config
        self.assertIsInstance(ontology, helpers.Ontology)

    @ignore_warnings
    def test_failed_ontology(self):
        with self.assertRaises(coreapi.exceptions.ErrorMessage):
            self.client.ontology('non_existing_ontology')
