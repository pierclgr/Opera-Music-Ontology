from rdflib import Graph, Namespace
from rdflib.namespace import RDF, RDFS, DC, OWL
from rdflib.term import URIRef, Literal
from scrape_data import scrape_opera_database, scrape_cross_composer, scrape_cross_era
import os
import zipfile

# define useful prefixes
PROTOCOL = 'https'
DOMAIN = 'w3id.org/ocm'
FORMAT_ONTOLOGY = 'ontology'
FORMAT_TYPE_RESOURCE = 'resources'

# define useful folder paths
ontology_file_path = "../ontologies/ontology.owl"
dataset_file_path = "../data/data.zip"

# define namespace for ontology entities and properties
ocm = Namespace(f"{PROTOCOL}://{DOMAIN}/{FORMAT_ONTOLOGY}/")

# define namespace for ontology resources
ocm_resource = Namespace(f"{PROTOCOL}://{DOMAIN}/{FORMAT_TYPE_RESOURCE}/")

######## EDIT FROM HERE ########

########## DATA PREPARATION ##########

print("########## DATA PREPARATION ##########")

# unzipping datasets in the data folder if present
if os.path.isfile(dataset_file_path):
    with zipfile.ZipFile(dataset_file_path, "r") as zip_ref:
        zip_ref.extractall("../data")

# download opera database from the web using scraping script and load
print("Loading Opera database...")
operadb_operas = scrape_opera_database(category="operas")
operadb_zarzuela = scrape_opera_database(category="zarzuela")
operadb_arias = scrape_opera_database(category="arias")
operadb_zarzuela_arias = scrape_opera_database(category="zarzuela_arias")
operadb_art_songs = scrape_opera_database(category="art_songs")
print("Done!")

# load cross-composer dataset from the web
print("Loading Cross-Composer dataset...")
cross_composer = scrape_cross_composer()
print("Done!")

# load cross-era dataset from the web
print("Loading Cross-Era dataset...")
cross_era = scrape_cross_era()
print("Done!")

########## KNOWLEDGE GRAPH CREATION ##########

print("########## KNOWLEDGE GRAPH CREATION ##########")
ontology = Graph().parse(ontology_file_path, format="n3")
knowledge_graph = Graph()

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
if not os.path.isdir("../ontologies"):
    os.mkdir("../ontologies")
final_graph.serialize(destination="../ontologies/final_graph.ttl", format='turtle')
