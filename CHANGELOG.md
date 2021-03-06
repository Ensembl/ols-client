CHANGELOG
=========

v1.0.0
------

- Initial version
- Ontologies list / details
- Term list / details
- Individuals list / details
- Properties list / details
- Basic Term search 
    
v1.0.1
------

- Added Term links exploring (Term defined relations)
- Added slice capability on lists
- Corrected github link
- Minor correction
- Mixed elements for search items
- Shortcuts methods on helpers classes
- Added __repr__ for lists
- fixed relations
- Detail client may return a list of element when retrievind multiple values for identifier, added unique parameter 
   (default False) to retrieve the defining ontology one, or first found if not - use cautiously
   
v1.0.2
------

- Updated documentation for BaseClient
- Updated some tests
- Added slice capability to ListClient
- Removed __main__ from Client
- Corrected relation types loading
- Updated Apache LICENSE copyright - Added NOTICE reference in code

v1.0.3
-----

- Changes page size to 1000 by default

v1.0.4
------

- Fixed: bug in getting sliced data (wrong base uri)

v1.0.5
------

- Fixed wrong str representation for Property
- Corrected Detail client to use pagination while searching item unique and list returned


v1.0.6
------

- Added individuals/individual client.
- Added properties/property client.
- Added more logging
- Added test
- Removed obsoletes helpers
- Added 5 retries in case of remote server errors
 
 v1.0.7
 ------
 
- Added extra path to term namespace access from API result (annotation/obo_namespace and annotation/namespace)
- Deprecated Term.obo_name_space property, replace by Term.namespace
- Added kwargs parameters parsing in Search allowing now client.search(query='tada',type='property',...)
- Fixed Search Filtering issues
 
 v1.0.8
 ------
  
 - Added extra way to retrieve term definition if not set under description (retrieve from annotation)
 - When searching for a detailed item (such as property), return the first 'in defining ontology' or first one if not found
 - Added PropertyAnnotation parsing
 
 v1.1.0
 ------
 
 - Refactored tests against a docker image instead of using public OLS api
 - Refactored client classes to avoid concrete class inheritance
 - Force retrieving `coreapi.document.Document` objects
 
 