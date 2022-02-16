from rdflib import Graph, Namespace
from rdflib.namespace import RDF, RDFS, DC, OWL
from rdflib.term import URIRef, Literal
import os

# define useful prefixes
PROTOCOL = 'https'
DOMAIN = 'w3id.org/ocm'
FORMAT_ONTOLOGY = 'ontology'
FORMAT_TYPE_RESOURCE = 'resources'

# define useful folder paths
ontology_file_path = "./ontologies/ontology.owl"

# define namespace for ontology entities and properties
ocm = Namespace(f"{PROTOCOL}://{DOMAIN}/{FORMAT_ONTOLOGY}/")

# define namespace for ontology resources
ocm_resource = Namespace(f"{PROTOCOL}://{DOMAIN}/{FORMAT_TYPE_RESOURCE}/")

ontology = Graph().parse(ontology_file_path, format="n3")
knowledge_graph = Graph()


######## EDIT FROM HERE ########

knowledge_graph.add((
    URIRef(f"{ocm_resource.Composer}/riccardo"),
    RDF.type,
    URIRef(f"{ocm.Composer}")
))

knowledge_graph.add((
    URIRef(f"{ocm_resource.Composer}/riccardo"),
    RDFS.label,
    Literal("riccardo")
))

knowledge_graph.add((
    URIRef(f"{ocm_resource.ClassicalSong}/quarantao"),
    RDF.type,
    URIRef(f"{ocm.ClassicalSong}")
))

knowledge_graph.add((
    URIRef(f"{ocm_resource.ClassicalSong}/quarantao"),
    RDFS.label,
    Literal("quarantao")
))

knowledge_graph.add((
    URIRef(f"{ocm_resource.Composer}/riccardo"),
    ocm.composerOf,
    URIRef(f"{ocm_resource.ClassicalSong}/quarantao")
))

######## TO HERE ########


final_graph = ontology + knowledge_graph
final_graph.bind("ocm", ocm)
print("######################################################################")
print(" protege graph statements: {}".format(len(ontology)))
print(" knowledge graph statements: {}".format(len(knowledge_graph)))
print(" > final graph statements: {}".format(len(final_graph)))
print("######################################################################")

# Serialize graph to .ttl files
if not os.path.isdir("./ontologies"): os.mkdir("./ontologies")
final_graph.serialize(destination="./ontologies/final_graph.ttl", format='turtle')