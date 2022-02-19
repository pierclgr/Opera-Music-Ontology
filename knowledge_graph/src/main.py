import pandas as pd
from rdflib import Graph, Namespace
from rdflib.namespace import RDF, OWL
from rdflib.term import URIRef, Literal
from scrape_data import scrape_opera_database, scrape_cross_composer, scrape_cross_era
import os
import zipfile
import re
from tqdm.auto import tqdm
from string import punctuation
from utils import *

# define useful prefixes
PROTOCOL = 'https'
DOMAIN = 'w3id.org/ocm'
FORMAT_ONTOLOGY = 'ontology'
FORMAT_TYPE_RESOURCE = 'resources'

# define useful folder paths
ONTOLOGY_FILE_PATH = "../ontologies/ontology.owl"
DATASET_FILE_PATH = "../data/data.zip"

# define useful links
NATIONALITY_MAP_PATH = "../data/demonyms.txt"

# load nationality map
nationality_map = pd.read_csv(NATIONALITY_MAP_PATH, sep=',', keep_default_na=False, header=None)
nationality_map.columns = ['Nationality', 'State']
nationality_map = dict(zip(nationality_map['Nationality'], nationality_map['State']))

# define namespace for ontology entities and properties
ocm = Namespace(f"{PROTOCOL}://{DOMAIN}/{FORMAT_ONTOLOGY}/")

# define namespace for ontology resources
ocm_resource = Namespace(f"{PROTOCOL}://{DOMAIN}/{FORMAT_TYPE_RESOURCE}/")




########## DATA PREPARATION ##########

print("########## DATA PREPARATION ##########")

# unzipping datasets in the data folder if present
if os.path.isfile(DATASET_FILE_PATH):
    with zipfile.ZipFile(DATASET_FILE_PATH, "r") as zip_ref:
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
ontology = Graph().parse(ONTOLOGY_FILE_PATH, format="n3")
# arco = Namespace("https://w3id.org/arco/ontology/arco/")

knowledge_graph = Graph()
# create situation creators
performance = SituationCreator(situa_type="performance")
music_creation = SituationCreator(situa_type="music_creation")





# OPERA DATABASE
# Loading data from opera database operas and zarzuelas
# - composer, nationality, lifetime
# - opera
# - premiere date
# - opera language
# - music sheet, synopsis, wiki, libretto
# situations -> music creation, performance
operadb_operas_zarzuela = pd.concat([operadb_operas, operadb_zarzuela])

print("Mapping Opera Database Operas and Zarzuelas...")
r = re.compile(r'[{}]+'.format(re.escape(punctuation)))
for id, row in tqdm(operadb_operas_zarzuela.iterrows(), total=len(operadb_operas_zarzuela)):

    # extract composers name and surname and id
    composers = row.Composer.split("; ")
    lifetime = row['Composer lifetime'].split("; ") if row['Composer lifetime'] != "" else None
    nationality = row['Composer nationality'].split("; ") if row['Composer nationality'] != "" else None
    composer_wiki = row["Composer Wikipedia"].split("; ") if row["Composer Wikipedia"] != "" else None
    list_of_composers = {}
    i = 0
    for composer in composers:
        if composer != "":
            composer = composer.replace("_", "").split(", ")
            if len(composer) > 2:
                name = f"{composer[2]} {composer[0]}"
                surname = composer[1]
            else:
                name = composer[1]
                surname = composer[0]
            composer = f"{name} {surname}".strip(" ")

            # extract artistic name if exists
            real_name = None
            if re.match("\[(.*?)\]", composer):
                artistic_name = re.search("\[(.*?)\]", composer).group(1)
                real_name = re.sub("\[(.*?)\]", "", composer).strip(" ")
                composer = artistic_name

            if re.match(".*\([Pp]seudonym of .*\).*", composer):
                real_name = re.search("\([Pp]seudonym of (.*?)\)", composer).group(1)
                real_name = None if real_name == "?" else real_name
                artistic_name = re.sub(" *\([Pp]seudonym of .*\) *", " ", composer).strip(" ")
                composer = artistic_name

            composer = composer.replace("[", "").replace("]", "")
            composer_id = r.sub('', composer).replace(" ", "_")

            # extract composer lifetime
            born = None
            death = None
            if lifetime:
                if i < len(lifetime):
                    cur_lifetime = lifetime[i]
                    if cur_lifetime != "":
                        cur_lifetime = cur_lifetime.split("-")
                        if len(cur_lifetime) < 2:
                            born = cur_lifetime[0].replace("?", "")
                        else:
                            born = cur_lifetime[0].replace("?", "")
                            death = cur_lifetime[1].replace("?", "")

            # extract composer state
            state = None
            if nationality:
                if i < len(nationality):
                    cur_nationality = nationality[i]
                    if cur_nationality != "":
                        cur_nationality = cur_nationality.replace("South", "South African")
                        cur_nationality = cur_nationality.replace("Korean", "South Korean")
                        cur_nationality = cur_nationality.replace("Yugoslavian", "Yugoslav")
                        cur_nationality = cur_nationality.replace("New", "New Zealander")
                        cur_nationality = cur_nationality.replace("Puerto", "Puerto Rican")
                        cur_nationality = cur_nationality.replace("Sierra", "Sierra Leonean")
                        state = nationality_map[cur_nationality]

            # extract composer wiki
            cur_composer_wiki = None
            if composer_wiki:
                if i < len(composer_wiki):
                    cur_composer_wiki = composer_wiki[i]
            list_of_composers[composer_id] = [composer, real_name, born, death, state, cur_composer_wiki]
        i += 1

    # extract opera title
    opera = row.Opera
    opera_id = r.sub('_', opera).replace(" ", "_").strip("_").strip(
        "'").title() if opera != "" and opera != "?" else None

    # extract opera premiere date
    date = row.Date.replace("n.d.", "").replace("?", "") if row.Date != "" else None

    # extract opera language
    language = row.Language.replace("?", "").replace("0", "") if row.Language != "" else None
    if language == "h" or language == "0":
        language = None

    # extract opera links
    sheet = row.Sheet if row.Sheet != "" else None
    synopsis = row.Synopsis if row.Synopsis != "" else None
    wiki = row.Wikipedia if row.Wikipedia != "" else None
    libretto = row.Libretto if row.Libretto != "" else None

    # ---- add triples ---- #
    # create ids for performance situation and music creation situation
    # something important info about performance are missing: just use an incremental value
    

    # add opera
    if opera_id:
        music_creation_id = music_creation.new("__".join(list(list_of_composers.keys())))

        # music creation situation
        knowledge_graph.add((
            URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
            RDF.type,
            ocm.MusicWriting
        ))

        libretto_id = "Libretto_" + opera_id

        knowledge_graph.add((
            URIRef(f"{ocm_resource.Opera}/{opera_id}"),
            RDF.type,
            ocm.Opera
        ))

        # add opera to music creation
        knowledge_graph.add((
            URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
            ocm.creates,
            URIRef(f"{ocm_resource.Opera}/{opera_id}")
        ))

        # add title to opera
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Opera}/{opera_id}"),
            ocm.hasTitle,
            Literal(opera.title())
        ))

        # add synopsis to opera
        if synopsis:
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Opera}/{opera_id}"),
                ocm.hasSynopsis,
                Literal(synopsis)
            ))

        # add wiki to opera
        if wiki:
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Opera}/{opera_id}"),
                ocm.hasWiki,
                Literal(wiki)
            ))

        # add sheet to opera
        if sheet:
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Opera}/{opera_id}"),
                ocm.hasMusicSheet,
                Literal(sheet)
            ))

        # add libretto of the opera
        if libretto:
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Libretto}/{libretto_id}"),
                RDF.type,
                ocm.Libretto
            ))

            # add libretto to the opera
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Opera}/{opera_id}"),
                ocm.hasLyric,
                URIRef(f"{ocm_resource.Libretto}/{libretto_id}")
            ))

            #  add link of the libretto
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Libretto}/{libretto_id}"),
                ocm.hasDocument,
                Literal(libretto)
            ))

            # add language of the libretto
            if language:
                knowledge_graph.add((
                    URIRef(f"{ocm_resource.Libretto}/{libretto_id}"),
                    ocm.hasLanguage,
                    Literal(language)
                ))

        if date:
            performance_id = performance.new(keyword="")

            # performance situation
            knowledge_graph.add((
                URIRef(f"{ocm_resource.TheatricalPerformance}/{performance_id}"),
                RDF.type,
                ocm.TheatricalPerformance
            ))

            # date of premier for the situation 
            knowledge_graph.add((
                URIRef(f"{ocm_resource.TheatricalPerformance}/{performance_id}"),
                ocm.yearOfPerformance,
                Literal(date)
            ))

            # opera involved in performance
            knowledge_graph.add((
                URIRef(f"{ocm_resource.TheatricalPerformance}/{performance_id}"),
                ocm.involvesComposition,
                URIRef(f"{ocm_resource.Opera}/{opera_id}"),
            ))


    # add composer to graph
    for k, v in list_of_composers.items():
        composer_id = k
        composer = v[0]
        real_name = v[1]
        born = v[2]
        death = v[3]
        state = v[4]
        composer_wiki = v[5]

        # composer id
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Composer}/{composer_id}"),
            RDF.type,
            ocm.Composer
        ))

        # composer name
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Composer}/{composer_id}"),
            ocm.hasName,
            Literal(composer)
        ))

        # add additional name
        if real_name:
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Composer}/{composer_id}"),
                ocm.hasName,
                Literal(real_name)
            ))

        # add birth date
        if born:
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Composer}/{composer_id}"),
                ocm.hasYearOfBirth,
                Literal(born)
            ))

        # add death date
        if death:
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Composer}/{composer_id}"),
                ocm.hasYearOfDeath,
                Literal(death)
            ))

        # add composer nationality
        if state:
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Composer}/{composer_id}"),
                ocm.isFrom,
                Literal(state)
            ))

        # add wiki link
        if composer_wiki:
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Composer}/{composer_id}"),
                ocm.hasWiki,
                Literal(composer_wiki)
            ))

        # add composer to music creation
        if opera_id:
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Composer}/{composer_id}"),
                ocm.involvedInCreation,
                URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
            ))


        


# OPERA DATABASE - Aria e Zarzuela Arias
# Loading data from opera database operas and zarzuelas
# - composer, nationality, lifetime
# - aria
# - opera
# - opera language
# - music sheet, synopsis, wiki, libretto
# situations -> music creation
operadb_arias_zarias = pd.concat([operadb_arias, operadb_zarzuela_arias])

print("Mapping Opera Database Arias and Zarzuela Arias...")

for id, row in tqdm(operadb_arias_zarias.iterrows(), total=len(operadb_arias_zarias)):

    # extract composers name and surname and id
    composers = row.Composer.split("; ")
    lifetime = row['Composer lifetime'].split("; ") if row['Composer lifetime'] != "" else None
    nationality = row['Composer nationality'].split("; ") if row['Composer nationality'] != "" else None
    composer_wiki = row["Composer Wikipedia"].split("; ") if row["Composer Wikipedia"] != "" else None
    list_of_composers = {}
    i = 0
    for composer in composers:
        if composer != "":
            composer = composer.replace("_", "").split(", ")
            if len(composer) > 2:
                name = f"{composer[2]} {composer[0]}"
                surname = composer[1]
            else:
                name = composer[1]
                surname = composer[0]
            composer = f"{name} {surname}".strip(" ")

            # extract artistic name if exists
            real_name = None
            if re.match("\[(.*?)\]", composer):
                artistic_name = re.search("\[(.*?)\]", composer).group(1)
                real_name = re.sub("\[(.*?)\]", "", composer).strip(" ")
                composer = artistic_name

            composer = composer.replace("[", "").replace("]", "")
            composer_id = r.sub('', composer).replace(" ", "_")

            # extract composer lifetime
            born = None
            death = None
            if lifetime:
                if i < len(lifetime):
                    cur_lifetime = lifetime[i]
                    if cur_lifetime != "":
                        cur_lifetime = cur_lifetime.split("-")
                        if len(cur_lifetime) < 2:
                            born = cur_lifetime[0].replace("?", "")
                        else:
                            born = cur_lifetime[0].replace("?", "")
                            death = cur_lifetime[1].replace("?", "")

            # extract composer state
            state = None
            if nationality:
                if i < len(nationality):
                    cur_nationality = nationality[i]
                    if cur_nationality != "":
                        cur_nationality = cur_nationality.replace("South", "South African")
                        cur_nationality = cur_nationality.replace("Korean", "South Korean")
                        cur_nationality = cur_nationality.replace("Yugoslavian", "Yugoslav")
                        cur_nationality = cur_nationality.replace("New", "New Zealander")
                        cur_nationality = cur_nationality.replace("Puerto", "Puerto Rican")
                        cur_nationality = cur_nationality.replace("Sierra", "Sierra Leonean")
                        state = nationality_map[cur_nationality]

            # extract composer wiki
            cur_composer_wiki = None
            if composer_wiki:
                if i < len(composer_wiki):
                    cur_composer_wiki = composer_wiki[i]
            list_of_composers[composer_id] = [composer, real_name, born, death, state, cur_composer_wiki]
        i += 1


    
    # extract opera title
    opera = row.Opera
    opera_id = r.sub('_', opera).replace(" ", "_").strip("_").strip(
        "'").title() if opera != "" and opera != "?" else None

    # extract aria title
    aria = row.Aria
    aria_id = r.sub("_", aria).replace(" ", "_").strip("_").strip(
        "'").title() if aria != "" and aria != "?" else None

    # extract character title
    character = None
    character_id = None
    if row.Character != "":
        character = row.Character
        character_id = r.sub("", character).replace(" ", "_")

    # extract voices 
    voices = []
    if row.Voice != "":
        for voice in row.Voice.title().split("/"):
            voices.append(voice.strip())


    # --- adding triples --- #
    
    if opera_id:
        # add opera
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Opera}/{opera_id}"),
            RDF.type,
            URIRef(ocm.Opera)
        ))

        knowledge_graph.add((
            URIRef(f"{ocm_resource.Opera}/{opera_id}"),
            ocm.hasTitle,
            Literal(opera.title())
        ))

        

    if aria_id:
        # add Aria
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Aria}/{aria_id}"),
            RDF.type,
            URIRef(ocm.Aria)
        ))

        # aria title
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Aria}/{aria_id}"),
            ocm.hasTitle,
            Literal(aria.title())
        ))
  
        # aria part of opera
        if opera_id:
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Aria}/{aria_id}"),
                ocm.includedInCollection,
                URIRef(f"{ocm_resource.Opera}/{opera_id}"),
            ))

        if character_id:
            # create character
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Character}/{character_id}"),
                RDF.type,
                URIRef(f"{ocm.Character}")
            ))

            # character name
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Character}/{character_id}"),
                ocm.hasCharacterName,
                Literal(character)
            ))

            # add character to aria
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Character}/{character_id}"),
                ocm.characterOf,
                URIRef(f"{ocm_resource.Aria}/{aria_id}")
            ))

            # add vocal score(s)
            for voice in voices:

                voice_id = voice.replace(" ", "_").title()
                score_id = f"{voice_id}_score_{aria_id}"
                
                # create vocal score
                knowledge_graph.add((
                    URIRef(f"{ocm_resource.VocalScore}/{score_id}"),
                    RDF.type,
                    ocm.VocalScore
                ))

                # vocal score for voice (instrument)
                knowledge_graph.add((
                    URIRef(f"{ocm_resource.VocalScore}/{score_id}"),
                    ocm.scoreForInstrument,
                    URIRef(f"{ocm_resource.Voice}/{voice_id}")
                ))

                # add score to aria
                knowledge_graph.add((
                    URIRef(f"{ocm_resource.VocalScore}/{score_id}"),
                    ocm.scoreOfSong,
                    URIRef(f"{ocm_resource.Aria}/{aria_id}")
                ))

    
    # add composer to graph
    for k, v in list_of_composers.items():
        composer_id = k
        composer = v[0]
        real_name = v[1]
        born = v[2]
        death = v[3]
        state = v[4]
        composer_wiki = v[5]

        # create composer
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Composer}/{composer_id}"),
            RDF.type,
            URIRef(f"{ocm.Composer}")
        ))

        # composer name
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Composer}/{composer_id}"),
            ocm.hasName,
            Literal(composer)
        ))

        # composer 2nd name
        if real_name:
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Composer}/{composer_id}"),
                ocm.hasName,
                Literal(real_name)
            ))

        # composer birth
        if born:
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Composer}/{composer_id}"),
                ocm.hasYearOfBirth,
                Literal(born)
            ))

        # composer death
        if death:
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Composer}/{composer_id}"),
                ocm.hasYearOfDeath,
                Literal(death)
            ))

        # composer from
        if state:
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Composer}/{composer_id}"),
                ocm.isFrom,
                Literal(state)
            ))

        # composer wiki
        if composer_wiki:
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Composer}/{composer_id}"),
                ocm.hasWiki,
                Literal(composer_wiki)
            ))

        if aria_id or opera_id:
            music_creation_id = music_creation.new("__".join(list(list_of_composers.keys())))

            # music creation situation
            knowledge_graph.add((
                URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
                RDF.type,
                ocm.MusicWriting
            ))

            # composer (subclass of author) in music creation
            knowledge_graph.add((
                URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
                ocm.involvesAuthor,
                URIRef(f"{ocm_resource.Composer}/{composer_id}"),
            ))
            
            # add aria to musical creation
            if aria_id:
                knowledge_graph.add((
                    URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
                    ocm.creates,
                    URIRef(f"{ocm_resource.Aria}/{aria_id}")
                ))

            # add opera to musical creation
            if opera_id:
                knowledge_graph.add((
                    URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
                    ocm.creates,
                    URIRef(f"{ocm_resource.Opera}/{opera_id}")
                ))






# # OPERA DATABASE - Art Song
# # Loading data from opera database operas and zarzuelas
# # - composer, nationality, lifetime
# # - aria
# # - album
# # - opera language(s)
# # - song voice(s)
# # - music sheet, synopsis, wiki, libretto
# # situations -> music creation
# operadb_arias_zarias = pd.concat([operadb_arias, operadb_zarzuela_arias])

# print("Mapping Opera Database Arias and Zarzuela Arias...")

# for id, row in tqdm(operadb_arias_zarias.iterrows(), total=len(operadb_arias_zarias)):

#     # extract composers name and surname and id
#     composers = row.Composer.split("; ")
#     lifetime = row['Composer lifetime'].split("; ") if row['Composer lifetime'] != "" else None
#     nationality = row['Composer nationality'].split("; ") if row['Composer nationality'] != "" else None
#     composer_wiki = row["Composer Wikipedia"].split("; ") if row["Composer Wikipedia"] != "" else None
#     list_of_composers = {}
#     i = 0
#     for composer in composers:
#         if composer != "":
#             composer = composer.replace("_", "").split(", ")
#             if len(composer) > 2:
#                 name = f"{composer[2]} {composer[0]}"
#                 surname = composer[1]
#             else:
#                 name = composer[1]
#                 surname = composer[0]
#             composer = f"{name} {surname}".strip(" ")

#             # extract artistic name if exists
#             real_name = None
#             if re.match("\[(.*?)\]", composer):
#                 artistic_name = re.search("\[(.*?)\]", composer).group(1)
#                 real_name = re.sub("\[(.*?)\]", "", composer).strip(" ")
#                 composer = artistic_name

#             composer = composer.replace("[", "").replace("]", "")
#             composer_id = r.sub('', composer).replace(" ", "_")

#             # extract composer lifetime
#             born = None
#             death = None
#             if lifetime:
#                 if i < len(lifetime):
#                     cur_lifetime = lifetime[i]
#                     if cur_lifetime != "":
#                         cur_lifetime = cur_lifetime.split("-")
#                         if len(cur_lifetime) < 2:
#                             born = cur_lifetime[0].replace("?", "")
#                         else:
#                             born = cur_lifetime[0].replace("?", "")
#                             death = cur_lifetime[1].replace("?", "")

#             # extract composer state
#             state = None
#             if nationality:
#                 if i < len(nationality):
#                     cur_nationality = nationality[i]
#                     if cur_nationality != "":
#                         cur_nationality = cur_nationality.replace("South", "South African")
#                         cur_nationality = cur_nationality.replace("Korean", "South Korean")
#                         cur_nationality = cur_nationality.replace("Yugoslavian", "Yugoslav")
#                         cur_nationality = cur_nationality.replace("New", "New Zealander")
#                         cur_nationality = cur_nationality.replace("Puerto", "Puerto Rican")
#                         cur_nationality = cur_nationality.replace("Sierra", "Sierra Leonean")
#                         state = nationality_map[cur_nationality]

#             # extract composer wiki
#             cur_composer_wiki = None
#             if composer_wiki:
#                 if i < len(composer_wiki):
#                     cur_composer_wiki = composer_wiki[i]
#             list_of_composers[composer_id] = [composer, real_name, born, death, state, cur_composer_wiki]
#         i += 1


    
#     # extract opera title
#     opera = row.Opera
#     opera_id = r.sub('_', opera).replace(" ", "_").strip("_").strip(
#         "'").title() if opera != "" and opera != "?" else None

#     # extract aria title
#     aria = row.Aria
#     aria_id = r.sub("_", aria).replace(" ", "_").strip("_").strip(
#         "'").title() if aria != "" and aria != "?" else None

#     # extract character title
#     character = None
#     character_id = None
#     if row.Character != "":
#         character = row.Character
#         character_id = r.sub("", character).replace(" ", "_")

#     # extract voices 
#     voices = []
#     if row.Voice != "":
#         for voice in row.Voice.title().split("/"):
#             voices.append(voice.strip())


#     # --- adding triples --- #
    
#     if opera_id:
#         # add opera
#         knowledge_graph.add((
#             URIRef(f"{ocm_resource.Opera}/{opera_id}"),
#             RDF.type,
#             URIRef(ocm.Opera)
#         ))

#         knowledge_graph.add((
#             URIRef(f"{ocm_resource.Opera}/{opera_id}"),
#             ocm.hasTitle,
#             Literal(opera.title())
#         ))

        

#     if aria_id:
#         # add Aria
#         knowledge_graph.add((
#             URIRef(f"{ocm_resource.Aria}/{aria_id}"),
#             RDF.type,
#             URIRef(ocm.Aria)
#         ))

#         # aria title
#         knowledge_graph.add((
#             URIRef(f"{ocm_resource.Aria}/{aria_id}"),
#             ocm.hasTitle,
#             Literal(aria.title())
#         ))
  
#         # aria part of opera
#         if opera_id:
#             knowledge_graph.add((
#                 URIRef(f"{ocm_resource.Aria}/{aria_id}"),
#                 ocm.includedInCollection,
#                 URIRef(f"{ocm_resource.Opera}/{opera_id}"),
#             ))

#         if character_id:
#             # create character
#             knowledge_graph.add((
#                 URIRef(f"{ocm_resource.Character}/{character_id}"),
#                 RDF.type,
#                 URIRef(f"{ocm.Character}")
#             ))

#             # character name
#             knowledge_graph.add((
#                 URIRef(f"{ocm_resource.Character}/{character_id}"),
#                 ocm.hasCharacterName,
#                 Literal(character)
#             ))

#             # add character to aria
#             knowledge_graph.add((
#                 URIRef(f"{ocm_resource.Character}/{character_id}"),
#                 ocm.characterOf,
#                 URIRef(f"{ocm_resource.Aria}/{aria_id}")
#             ))

#             # add vocal score(s)
#             for voice in voices:

#                 voice_id = voice.replace(" ", "_").title()
#                 score_id = f"{voice_id}_score_{aria_id}"
                
#                 # create vocal score
#                 knowledge_graph.add((
#                     URIRef(f"{ocm_resource.VocalScore}/{score_id}"),
#                     RDF.type,
#                     ocm.VocalScore
#                 ))

#                 # vocal score for voice (instrument)
#                 knowledge_graph.add((
#                     URIRef(f"{ocm_resource.VocalScore}/{score_id}"),
#                     ocm.scoreForInstrument,
#                     URIRef(f"{ocm_resource.Voice}/{voice_id}")
#                 ))

#                 # add score to aria
#                 knowledge_graph.add((
#                     URIRef(f"{ocm_resource.VocalScore}/{score_id}"),
#                     ocm.scoreOfSong,
#                     URIRef(f"{ocm_resource.Aria}/{aria_id}")
#                 ))

    
#     # add composer to graph
#     for k, v in list_of_composers.items():
#         composer_id = k
#         composer = v[0]
#         real_name = v[1]
#         born = v[2]
#         death = v[3]
#         state = v[4]
#         composer_wiki = v[5]

#         # create composer
#         knowledge_graph.add((
#             URIRef(f"{ocm_resource.Composer}/{composer_id}"),
#             RDF.type,
#             URIRef(f"{ocm.Composer}")
#         ))

#         # composer name
#         knowledge_graph.add((
#             URIRef(f"{ocm_resource.Composer}/{composer_id}"),
#             ocm.hasName,
#             Literal(composer)
#         ))

#         # composer 2nd name
#         if real_name:
#             knowledge_graph.add((
#                 URIRef(f"{ocm_resource.Composer}/{composer_id}"),
#                 ocm.hasName,
#                 Literal(real_name)
#             ))

#         # composer birth
#         if born:
#             knowledge_graph.add((
#                 URIRef(f"{ocm_resource.Composer}/{composer_id}"),
#                 ocm.hasYearOfBirth,
#                 Literal(born)
#             ))

#         # composer death
#         if death:
#             knowledge_graph.add((
#                 URIRef(f"{ocm_resource.Composer}/{composer_id}"),
#                 ocm.hasYearOfDeath,
#                 Literal(death)
#             ))

#         # composer from
#         if state:
#             knowledge_graph.add((
#                 URIRef(f"{ocm_resource.Composer}/{composer_id}"),
#                 ocm.isFrom,
#                 Literal(state)
#             ))

#         # composer wiki
#         if composer_wiki:
#             knowledge_graph.add((
#                 URIRef(f"{ocm_resource.Composer}/{composer_id}"),
#                 ocm.hasWiki,
#                 Literal(composer_wiki)
#             ))

#         if aria_id or opera_id:
#             music_creation_id = music_creation.new("__".join(list(list_of_composers.keys())))

#             # music creation situation
#             knowledge_graph.add((
#                 URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
#                 RDF.type,
#                 ocm.MusicWriting
#             ))

#             # composer (subclass of author) in music creation
#             knowledge_graph.add((
#                 URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
#                 ocm.involvesAuthor,
#                 URIRef(f"{ocm_resource.Composer}/{composer_id}"),
#             ))
            
#             # add aria to musical creation
#             if aria_id:
#                 knowledge_graph.add((
#                     URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
#                     ocm.creates,
#                     URIRef(f"{ocm_resource.Aria}/{aria_id}")
#                 ))

#             # add opera to musical creation
#             if opera_id:
#                 knowledge_graph.add((
#                     URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
#                     ocm.creates,
#                     URIRef(f"{ocm_resource.Opera}/{opera_id}")
#                 ))

            


######## TO HERE ########

final_graph = ontology + knowledge_graph
final_graph.bind("ocm", ocm)
# final_graph.bind("arco", arco)
print("######################################################################")
print("Ontology statements: {}".format(len(ontology)))
print("Knowledge graph statements: {}".format(len(knowledge_graph)))
print("> Final graph statements: {}".format(len(final_graph)))
print("######################################################################")

# Serialize graph to .ttl files
print("Saving final graph...")
if not os.path.isdir("../ontologies"):
    os.mkdir("../ontologies")
final_graph.serialize(destination="../ontologies/final_graph.ttl", format='turtle')
print("Done!")
