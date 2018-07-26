OLS Ontologies loader 
=====================

Provide class based client for accessing OLS RestAPI from EMBL-EBI

Install
------- 

with pip

```bash
    pip install ebi-ols-client
```
    
See: https://www.ebi.ac.uk/ols/docs/api for more information on OLS API

Main files
----------

    - ebi.ols.api.client.py: contains main classes to access OLS via HAL schema.
    - ebi.ols.api.helpers.py: data tranfer object loaded from API calls
    
How to use
---------- 

```python

from ebi.ols.api.client import OlsClient

client = OlsClient()
ontology = client.ontology('fpo')

terms = ontology.terms()
individuals = ontology.individuals()
properties = ontology.properties()

# work with all 'list' item types (terms, individuals, properties
for term in terms:
    # do whatever
    print(term)

# Direct List'like access on all list types
term = terms[1254]
individual = individuals[123]
# ...