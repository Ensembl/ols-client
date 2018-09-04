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
    