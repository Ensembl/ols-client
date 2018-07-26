# 3. looping over list

Date: 2018-07-26

## Status

Done

## Context

We want to be able to loop simply over Ontologies / Terms results, without bothering if a
new call is made to change page.  

OLS API results are paginated, the page size is a parameter in Query.
There is no simple way to loop over all elements, and returning all results is not a solution, considering amount of data
The actual calls to API are hidden from final users.

```python

from ebi.ols.api.client import OlsClient

client = OlsClient()
ontology = client.ontology('fpo')

terms = ontology.terms()
individuals = ontology.individuals()
properties = ontology.properties()

# work with all 'list' item types
for term in terms:
    # do whatever
    print(term)

# Direct List'like access on all list types
term = terms[1254]
individual = individuals[123]
# ...

```  

## Decision

To Implement

## Consequences

- [~] The list must keep track of current loaded, therefore if initial request  
- [~] ListMixin object are state-full. 
