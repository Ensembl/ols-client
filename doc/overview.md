OLS API CLIENT
==============

Project is aimed to provide a simple Python tool to interact with EMBL/EBI Ontology Lookup Service (OLS) located
at https://www.ebi.ac.uk/ols/index. via its REST API

Main goals are:

- simplify integration
- simplify users experience while using this library
- provide on another tool to interact with EMBL/EBI data

Use of standard client is strongly recommended while programmatically integrating our OLS service.

Exemple of use:
---------------

```python

from ebi.ols.api.client import OlsClient

client = OlsClient()
# load ontology
ontology = client.ontology('go')

# some filters may be added with a standard python dictionary
terms = ontology.terms() 

individuals = ontology.individuals()
properties = ontology.properties()

# work with all 'list' item types (terms, individuals, properties
for term in terms:
    # do whatever
    print(term)
    ancestors = term.ancestors()
    second_ancestor = ancestors[1]
    

# Direct List'like access on all list types
term = terms[1254]
individual = individuals[123]

## use search terms api entry
terms = client.search(query='transcriptome')
# terms is now a standard list of helpers.Term

# ...