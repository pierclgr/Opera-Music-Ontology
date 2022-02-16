# Opera Music Ontology
An ontology for opera musical heritage and musicological research.
 
This projects provides the following facilities for enhancing user experience: 
 - Virtuoso as SPARQL enpoint;
 - LODE for visualising ontologies as HTML;
 - LodLive and WebVOWL for visualising ontologies with the Visual Notation for OWL Ontologies (VOWL);
 - LodView for browsing ontology entities as well as controlled vocabularies entities.


### With Docker
The project relies on Docker. To build the containers type the following command in the terminal having the root of the project as base folder:
```
docker-compose build
```
To run the containers type the following command in the terminal having the root of the project as base folder:
```
docker-compose up
```

### Usage
Once the containers are up and assuming that `localhost` is the reference host, users can access:
 - Virtuoso SPARQL endpoint at http://localhost:8890/sparql
 - LodView at http://localhost:8080/lodview
 - LODE at http://localhost:9090/lode
 - WebVOWL at http://localhost:8888/webvowl
 - LodLive at http://localhost/app_en.html

<!-- #### Quick Examples:
Here are some quick links to show how information about the element
"https://w3id.org/stlab/ke/lifo/onto/Indicator" can be visualized using the browser:

 - Virtuoso: http://localhost:8890/sparql?query=select?p?o{%3Chttps://w3id.org/stlab/ke/lifo/onto/Indicator%3E?p?o}
 - LodView:  http://localhost:8080/lodview/onto/Indicator
 - Lode: http://localhost:9090/lode/extract?url=https://w3id.org/stlab/ke/lifo/onto/Indicator -->