import pandas as pd
from rdflib import Graph, Namespace
from rdflib.namespace import RDF, OWL, RDFS
from rdflib.term import URIRef, Literal
from scrape_data import scrape_opera_database, scrape_cross_composer, scrape_cross_era
import os
import zipfile
import re
from tqdm.auto import tqdm
from string import punctuation
from utils import *
import wget

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

        # add music creation label
        knowledge_graph.add((
            URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
            RDFS.label,
            Literal(music_creation_id.replace("_", " "))
        ))

        # add opera
        libretto_id = "Libretto_" + opera_id
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Opera}/{opera_id}"),
            RDF.type,
            ocm.Opera
        ))

        # add opera label
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Opera}/{opera_id}"),
            RDFS.label,
            Literal(opera.title())
        ))

        # add opera to music creation
        knowledge_graph.add((
            URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
            ocm.createsComposition,
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

            # add libretto label
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Libretto}/{libretto_id}"),
                RDFS.label,
                Literal(libretto_id.replace("_", " "))
            ))

            # add libretto to the opera
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Opera}/{opera_id}"),
                ocm.hasLyrics,
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
                URIRef(f"{ocm_resource.MusicalPerformance}/{performance_id}"),
                RDF.type,
                ocm.MusicalPerformance
            ))

            # add performance situation label
            knowledge_graph.add((
                URIRef(f"{ocm_resource.MusicalPerformance}/{performance_id}"),
                RDFS.label,
                Literal(performance_id.replace("_", " "))
            ))

            # date of premier for the situation
            knowledge_graph.add((
                URIRef(f"{ocm_resource.MusicalPerformance}/{performance_id}"),
                ocm.yearOfPerformance,
                Literal(date)
            ))

            # opera involved in performance
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Opera}/{opera_id}"),
                ocm.performedIn,
                URIRef(f"{ocm_resource.MusicalPerformance}/{performance_id}"),
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

        # composer type & id
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Composer}/{composer_id}"),
            RDF.type,
            ocm.Composer
        ))

        # add composer label
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Composer}/{composer_id}"),
            RDFS.label,
            Literal(composer)
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
                URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
                ocm.involvesAuthor,
                URIRef(f"{ocm_resource.Composer}/{composer_id}"),
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

    # extract opera wiki
    opera_wiki = row['Opera link'] if row['Opera link'] != "" else None

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

    # extract languages
    languages = [lang.strip() for lang in row.Language.strip().split(", ")]

    # --- adding triples --- #

    if opera_id:
        # add opera
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Opera}/{opera_id}"),
            RDF.type,
            URIRef(ocm.Opera)
        ))

        # add opera label
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Opera}/{opera_id}"),
            RDFS.label,
            Literal(opera.title())
        ))

        # add opera name
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Opera}/{opera_id}"),
            ocm.hasTitle,
            Literal(opera.title())
        ))

        # add opera link
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Opera}/{opera_id}"),
            ocm.hasWiki,
            Literal(opera_wiki)
        ))

    if aria_id:
        # add Aria
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Aria}/{aria_id}"),
            RDF.type,
            URIRef(ocm.Aria)
        ))

        # aria label
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Aria}/{aria_id}"),
            RDFS.label,
            Literal(aria)
        ))

        # aria title
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Aria}/{aria_id}"),
            ocm.hasTitle,
            Literal(aria)
        ))

        # aria sheet
        aria_sheet = row.Sheet if row.Sheet != "" else None
        if aria_sheet:
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Aria}/{aria_id}"),
                ocm.hasMusicSheet,
                Literal(aria_sheet)
            ))

        # aria part of opera
        if opera_id:
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Opera}/{opera_id}"),
                ocm.includesSong,
                URIRef(f"{ocm_resource.Aria}/{aria_id}"),
            ))

        if character_id:
            # create character
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Character}/{character_id}"),
                RDF.type,
                ocm.Character
            ))

            # character label
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Character}/{character_id}"),
                RDFS.label,
                Literal(character)
            ))

            # character name
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Character}/{character_id}"),
                ocm.hasCharacterName,
                Literal(character)
            ))

            # add character to aria
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Aria}/{aria_id}"),
                ocm.hasCharacter,
                URIRef(f"{ocm_resource.Character}/{character_id}"),
            ))

            # add vocal score(s)
            for voice in voices:
                voice_id = voice.replace(" ", "_").title()
                score_id = f"{voice_id}_score_{aria_id}"

                # create voice
                knowledge_graph.add((
                    URIRef(f"{ocm_resource.Voice}/{voice_id}"),
                    RDF.type,
                    ocm.Voice
                ))

                # add voice label
                knowledge_graph.add((
                    URIRef(f"{ocm_resource.Voice}/{voice_id}"),
                    RDFS.label,
                    Literal(voice_id)
                ))

                # create vocal score
                knowledge_graph.add((
                    URIRef(f"{ocm_resource.VocalScore}/{score_id}"),
                    RDF.type,
                    ocm.VocalScore
                ))

                # add vocal score label
                knowledge_graph.add((
                    URIRef(f"{ocm_resource.VocalScore}/{score_id}"),
                    RDFS.label,
                    Literal(score_id.replace("_", " "))
                ))

                # vocal score for voice (instrument)
                knowledge_graph.add((
                    URIRef(f"{ocm_resource.Voice}/{voice_id}"),
                    ocm.instrumentOfScore,
                    URIRef(f"{ocm_resource.VocalScore}/{score_id}"),
                ))

                # add score to aria
                knowledge_graph.add((
                    URIRef(f"{ocm_resource.Aria}/{aria_id}"),
                    ocm.hasScore,
                    URIRef(f"{ocm_resource.VocalScore}/{score_id}"),
                ))

                # create lyric
                lyric_id = f"{aria_id}__lyrics"
                knowledge_graph.add((
                    URIRef(f"{ocm_resource.Lyrics}/{lyric_id}"),
                    RDF.type,
                    ocm.Lyrics
                ))

                # add lyric label
                knowledge_graph.add((
                    URIRef(f"{ocm_resource.Lyrics}/{lyric_id}"),
                    RDFS.label,
                    Literal(lyric_id.replace("_", " "))
                ))

                # add lyrics to song
                knowledge_graph.add((
                    URIRef(f"{ocm_resource.Aria}/{aria_id}"),
                    ocm.hasLyrics,
                    URIRef(f"{ocm_resource.Lyrics}/{lyric_id}")
                ))

                for language in languages:
                    # add language(s) of lyrics
                    knowledge_graph.add((
                        URIRef(f"{ocm_resource.Lyrics}/{lyric_id}"),
                        ocm.hasLanguage,
                        Literal(language)
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
            ocm.Composer
        ))

        # add score label
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Composer}/{composer_id}"),
            RDFS.label,
            Literal(composer)
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

            # add music creation label
            knowledge_graph.add((
                URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
                RDFS.label,
                Literal(music_creation_id.replace("_", " "))
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
                    ocm.createsComposition,
                    URIRef(f"{ocm_resource.Aria}/{aria_id}")
                ))

            # add opera to musical creation
            if opera_id:
                knowledge_graph.add((
                    URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
                    ocm.createsComposition,
                    URIRef(f"{ocm_resource.Opera}/{opera_id}")
                ))

# OPERA DATABASE - Art Song
# Loading data from opera database operas and zarzuelas
# - composer, nationality, lifetime
# - aria
# - album
# - opera language(s)
# - song voice(s)
# - music sheet, synopsis, wiki, libretto
# situations -> music creation
print("Mapping Opera Database Art Song...")

for id, row in tqdm(operadb_art_songs.iterrows(), total=len(operadb_art_songs)):

    composer_name = " ".join(list(reversed(row.Composer.split(", "))))
    composer_id = composer_name.replace(" ", "_")
    composer_bdate = row["Composer lifetime"].replace(" ", "").split("-")[0]
    composer_ddate = row["Composer lifetime"].replace(" ", "").split("-")[1]
    composer_nationality = row["Composer nationality"].replace(" ", "")
    composer_from = nationality_map[composer_nationality].strip(" ")
    composer_wiki = row["Composer Wikipedia"]

    # song info
    song_title = row.Song
    song_title = re.sub(r"\s-\sD\d[0-9]*", "", song_title).strip("_")  # remove the " - D123" thing
    song_id = r.sub("_", song_title.title().replace(" ", "_").replace(".", "")).strip("_")

    # album
    album_title = row.Album.strip("'").strip("_") if row.Album != "" else None
    album_id = r.sub("_", album_title.replace(" ", "_").replace(".", "")) if album_title is not None else None

    # voices
    voices = row.Voice.strip().split(", ") if row.Voice != "" else []

    # sheets
    sheets = []
    for voice in voices:
        sheets.append(row[f"{voice.title()} Sheet"])

    # languages
    languages = [lang.strip() for lang in row.Language.strip().split(", ")]

    # --- adding triples --- #
    music_creation_id = music_creation.new(composer_id)

    # create song - ?
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Song}/{song_id}"),
        RDF.type,
        ocm.Song
    ))

    # add song label
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Song}/{song_id}"),
        RDFS.label,
        Literal(song_title)
    ))

    # song title
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Song}/{song_id}"),
        ocm.hasTitle,
        Literal(song_title)
    ))

    # music creation situation type
    knowledge_graph.add((
        URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
        RDF.type,
        ocm.MusicWriting
    ))

    # add music creation label
    knowledge_graph.add((
        URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
        RDFS.label,
        Literal(music_creation_id.replace("_", " "))
    ))

    # add song to music writing
    knowledge_graph.add((
        URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
        ocm.createsComposition,
        URIRef(f"{ocm_resource.Song}/{song_id}"),
    ))

    # create composer
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Composer}/{composer_id}"),
        RDF.type,
        ocm.Composer
    ))

    # composer label
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Composer}/{composer_id}"),
        RDFS.label,
        Literal(composer_name)
    ))

    # composer name
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Composer}/{composer_id}"),
        ocm.hasName,
        Literal(composer_name)
    ))

    # composer birth
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Composer}/{composer_id}"),
        ocm.hasYearOfBirth,
        Literal(composer_bdate)
    ))

    # composer death
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Composer}/{composer_id}"),
        ocm.hasYearOfDeath,
        Literal(composer_ddate)
    ))

    # composer wiki
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Composer}/{composer_id}"),
        ocm.hasWiki,
        Literal(composer_wiki)
    ))

    # composer is from
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Composer}/{composer_id}"),
        ocm.isFrom,
        Literal(composer_from)
    ))

    # add composer to music writing
    knowledge_graph.add((
        URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
        ocm.involvesAuthor,
        URIRef(f"{ocm_resource.Composer}/{composer_id}"),
    ))

    for voice, sheet in zip(voices, sheets):

        voice_score_id = f"{voice}_sore_{song_id}"

        # create voice score
        knowledge_graph.add((
            URIRef(f"{ocm_resource.VocalScore}/{voice_score_id}"),
            RDF.type,
            ocm.VocalScore
        ))

        # add voice score label
        knowledge_graph.add((
            URIRef(f"{ocm_resource.VocalScore}/{voice_score_id}"),
            RDFS.label,
            Literal(voice_score_id.replace("_", " "))
        ))

        # music sheet for vocal score
        knowledge_graph.add((
            URIRef(f"{ocm_resource.VocalScore}/{voice_score_id}"),
            ocm.hasMusicSheet,
            Literal(sheet)
        ))

        # vocal score for song
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Song}/{song_id}"),
            ocm.hasScore,
            URIRef(f"{ocm_resource.VocalScore}/{voice_score_id}"),
        ))

        # create voice as instrument
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Voice}/{voice}"),
            RDF.type,
            ocm.Voice
        ))

        # add RDFS label
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Voice}/{voice}"),
            RDFS.label,
            Literal(voice)
        ))

        # vocal score for voice
        knowledge_graph.add((
            URIRef(f"{ocm_resource.VocalScore}/{voice_score_id}"),
            ocm.socreForInstrument,
            URIRef(f"{ocm_resource.Voice}/{voice}"),
        ))

        # create lyric
        lyric_id = f"{song_id}__lyrics"
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Lyrics}/{lyric_id}"),
            RDF.type,
            ocm.Lyrics
        ))

        # add lyric label
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Lyrics}/{lyric_id}"),
            RDFS.label,
            Literal(lyric_id.replace("_", " "))
        ))

        # add lyrics to song
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Song}/{song_id}"),
            ocm.hasLyrics,
            URIRef(f"{ocm_resource.Lyrics}/{lyric_id}")
        ))

        for language in languages:
            # add language(s) of lyrics
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Lyrics}/{lyric_id}"),
                ocm.hasLanguage,
                Literal(language)
            ))

    if album_id:
        # create album id
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Album}/{album_id}"),
            RDF.type,
            ocm.Album
        ))

        # add album label
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Album}/{album_id}"),
            RDFS.label,
            Literal(album_title)
        ))

        # add album wikipedia
        album_wikipedia = row["Album wikipedia"] if row['Album wikipedia'] != "" else None
        if album_wikipedia:
            knowledge_graph.add((
                URIRef(f"{ocm_resource.Album}/{album_id}"),
                ocm.hasWiki,
                Literal(album_wikipedia)
            ))

        # add album to music writing
        knowledge_graph.add((
            URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
            ocm.createsComposition,
            URIRef(f"{ocm_resource.Album}/{album_id}"),
        ))

        # add song to album
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Album}/{album_id}"),
            ocm.includesSong,
            URIRef(f"{ocm_resource.Song}/{song_id}"),
        ))

        # add title to album
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Album}/{album_id}"),
            ocm.hasTitle,
            Literal(album_title)
        ))

print("Mapping Cross Era...")
for id, row in tqdm(cross_era.iterrows(), total=len(cross_era)):

    # composer info
    composer_name = " ".join(list(reversed(row.Composer.split("; "))))
    composer_id = composer_name.replace(" ", "_").replace(".", "")
    composer_bdate = row.CompLifetime.replace(" ", "").split("-")[0]
    composer_ddate = row.CompLifetime.replace(" ", "").split("-")[1]
    composer_from = row.Country.replace(" ", "").split(";")

    # song info
    song_id = row.Filename.lower().replace(" ", "_").replace(".", "")
    song_title = row.Filename
    song_mode = row.Mode.lower() if type(row.Mode) == str else None
    song_key = row.Key if type(row.Key) == str else None

    # instrumentation
    instrum = row.Instrumentation.replace(".", "")
    instrum_type, score_type = get_instrument_type_and_score(instrum)
    score_id = f"{instrum}_score_{song_id}"

    # ----- creating individuals ----- #

    # situation
    music_creation_id = music_creation.new(composer_id)

    # composer type
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Composer}/{composer_id}"),
        RDF.type,
        ocm.Composer
    ))

    # composer label
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Composer}/{composer_id}"),
        RDFS.label,
        Literal(composer_name)
    ))

    # composer name
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Composer}/{composer_id}"),
        ocm.hasName,
        Literal(composer_name)
    ))

    # composer birth
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Composer}/{composer_id}"),
        ocm.hasYearOfBirth,
        Literal(composer_bdate)
    ))

    # composer death
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Composer}/{composer_id}"),
        ocm.hasYearOfDeath,
        Literal(composer_ddate)
    ))

    # composer is from
    for place in composer_from:
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Composer}/{composer_id}"),
            ocm.isFrom,
            Literal(place)
        ))

    # musical creation - create the situation
    knowledge_graph.add((
        URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
        RDF.type,
        ocm.MusicWriting
    ))

    # situation label
    knowledge_graph.add((
        URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
        RDFS.label,
        Literal(music_creation_id.replace("_", " "))
    ))

    # musical creation - involves author
    knowledge_graph.add((
        URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
        ocm.involvesAuthor,
        URIRef(f"{ocm_resource.Composer}/{composer_id}")
    ))

    # song id
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Song}/{song_id}"),
        RDF.type,
        ocm.Song
    ))

    # song label
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Song}/{song_id}"),
        RDFS.label,
        Literal(song_title)
    ))

    # song title
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Song}/{song_id}"),
        ocm.hasTitle,
        Literal(song_title)
    ))

    if song_mode is not None:
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Song}/{song_id}"),
            ocm.hasMode,
            Literal(song_mode)
        ))

    if song_key is not None:
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Song}/{song_id}"),
            ocm.hasKey,
            Literal(song_key)
        ))

    # song in music creation situation
    knowledge_graph.add((
        URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
        ocm.createsComposition,
        URIRef(f"{ocm_resource.Song}/{song_id}"),
    ))

    # add score
    knowledge_graph.add((
        URIRef(f"{ocm_resource}{score_type}/{score_id}"),
        RDF.type,
        URIRef(f"{ocm}{score_type}"),
    ))

    # add score label
    knowledge_graph.add((
        URIRef(f"{ocm_resource}{score_type}/{score_id}"),
        RDFS.label,
        Literal(score_id.replace("_", " "))
    ))

    # create score for instrument
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Song}/{song_id}"),
        ocm.hasScore,
        URIRef(f"{ocm_resource}{score_type}/{score_id}"),
    ))

    # create instrument
    knowledge_graph.add((
        URIRef(f"{ocm_resource}{instrum_type}/{instrum}"),
        RDF.type,
        URIRef(f"{ocm}{instrum_type}"),
    ))

    # add instrument label
    knowledge_graph.add((
        URIRef(f"{ocm_resource}{instrum_type}/{instrum}"),
        RDFS.label,
        Literal(f"{instrum}"),
    ))

    # add instrument to score
    knowledge_graph.add((
        URIRef(f"{ocm_resource}{instrum_type}/{instrum}"),
        ocm.instrumentOfScore,
        URIRef(f"{ocm_resource}{score_type}/{score_id}"),
    ))

print("Mapping Cross Composer...")
for id, row in tqdm(cross_composer.iterrows(), total=len(cross_composer)):

    # TODO usarne solo una per tutti i dataset
    performance_id = performance.new(
        keyword="")  # something important info about performance are missing: just use an incremental value

    composer_name = " ".join(list(reversed(row.Composer.split("; "))))
    composer_id = composer_name.replace(" ", "_")

    music_creation_id = music_creation.new(composer_id)

    # song info
    song_title = row.Filename
    song_id = song_title.title().replace(" ", "_").replace(".", "")

    # conductor(s)
    conductor_names = []
    conductor_ids = []
    if row.Conductor != "" and row.Conductor.strip() != "":
        for conductor in row.Conductor.split("; "):
            conductor_name = " ".join(list(reversed(conductor.split(", "))))
            conductor_id = conductor_name.replace(" ", "_")
            conductor_names.append(conductor_name)
            conductor_ids.append(conductor_id)

    # performer(s)
    performer_names = []
    performer_ids = []
    if row.Performer.strip() != "":
        for performer in row.Performer.split("; "):
            performer_name = " ".join(list(performer.split(", ")))
            performer_id = performer_name.replace(" ", "_")
            performer_names.append(performer_name)
            performer_ids.append(performer_id)

    # instrument(s)
    instruments = []
    if row.Instrumentation.strip() != "":
        for instrument in row.Instrumentation.split("; "):
            instruments.append(instrument)

    # album
    album_title = row.Album.strip("'").strip("_")
    album_id = album_title.replace(" ", "_").replace(".", "")

    #########

    # create song - ?
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Song}/{song_id}"),
        RDF.type,
        ocm.Song
    ))

    # add song label
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Song}/{song_id}"),
        RDFS.label,
        Literal(song_title)
    ))

    # song title
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Song}/{song_id}"),
        ocm.hasTitle,
        Literal(song_title)
    ))

    # create album - ?
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Album}/{album_id}"),
        RDF.type,
        ocm.Album
    ))

    # add album label
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Album}/{album_id}"),
        RDFS.label,
        Literal(album_title)
    ))

    # album title
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Album}/{album_id}"),
        ocm.hasTitle,
        Literal(album_title)
    ))

    # musical creation situation
    knowledge_graph.add((
        URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
        RDF.type,
        ocm.MusicWriting
    ))

    # create composer
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Composer}/{composer_id}"),
        RDF.type,
        ocm.Composer
    ))

    # add composer name
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Composer}/{composer_id}"),
        ocm.hasName,
        Literal(composer_name)
    ))

    # add composer name
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Composer}/{composer_id}"),
        RDFS.label,
        Literal(composer_name)
    ))

    # add composer to creation
    knowledge_graph.add((
        URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
        ocm.involvesAuthor,
        URIRef(f"{ocm_resource.Composer}/{composer_id}")
    ))

    # music situation labelì
    knowledge_graph.add((
        URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
        RDFS.label,
        Literal(music_creation_id.replace("_", " "))
    ))

    # add album to music creation
    knowledge_graph.add((
        URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
        ocm.createsComposition,
        URIRef(f"{ocm_resource.Album}/{album_id}"),
    ))

    # add song to album
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Album}/{album_id}"),
        ocm.includesSong,
        URIRef(f"{ocm_resource.Song}/{song_id}"),
    ))

    # add song to music creation
    knowledge_graph.add((
        URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
        ocm.createsComposition,
        URIRef(f"{ocm_resource.Song}/{song_id}"),
    ))

    # performance situation
    knowledge_graph.add((
        URIRef(f"{ocm_resource.MusicalPerformance}/{performance_id}"),
        RDF.type,
        ocm.MusicalPerformance
    ))

    # add performance label
    knowledge_graph.add((
        URIRef(f"{ocm_resource.MusicalPerformance}/{performance_id}"),
        RDFS.label,
        Literal(performance_id.replace("_", " "))
    ))

    # conductor type -- inferred?
    for conductor_id, conductor_name in zip(conductor_ids, conductor_names):
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Conductor}/{conductor_id}"),
            RDF.type,
            ocm.Conductor
        ))

        # conductor label
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Conductor}/{conductor_id}"),
            RDFS.label,
            Literal(conductor_name)
        ))

        # conductor name
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Conductor}/{conductor_id}"),
            ocm.hasName,
            Literal(conductor_name)
        ))

        # add conductor to performance
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Conductor}/{conductor_id}"),
            ocm.conductsPerformance,
            URIRef(f"{ocm_resource.MusicalPerformance}/{performance_id}"),
        ))

    # add song to performance -- inferred?
    knowledge_graph.add((
        URIRef(f"{ocm_resource.Song}/{song_id}"),
        ocm.performedIn,
        URIRef(f"{ocm_resource.MusicalPerformance}/{performance_id}"),
    ))

    for performer_name, performer_id, instrum in zip(performer_names,
                                                     performer_ids,
                                                     instruments):

        instrum_type, score_type = get_instrument_type_and_score(instrum)

        performer_type = None
        if instrum_type == "Voice":
            performer_type = "Singer"
        elif instrum_type == "PhysicalInstrument":
            performer_type = "Musician"

        # score type
        score_id = f"{instrum}_score_{song_id}"
        knowledge_graph.add((
            URIRef(f"{ocm_resource}{score_type}/{score_id}"),
            RDF.type,
            URIRef(f"{ocm}{score_type}")
        ))

        # add score label
        knowledge_graph.add((
            URIRef(f"{ocm_resource}{score_type}/{score_id}"),
            RDFS.label,
            Literal(score_id.replace("_", " "))
        ))

        # create instrument
        knowledge_graph.add((
            URIRef(f"{ocm_resource}{instrum_type}/{instrum}"),
            RDF.type,
            URIRef(f"{ocm}{instrum_type}"),
        ))

        # create instrument label
        knowledge_graph.add((
            URIRef(f"{ocm_resource}{instrum_type}/{instrum}"),
            RDFS.label,
            Literal(f"{instrum}")
        ))

        # add instrument to score
        knowledge_graph.add((
            URIRef(f"{ocm_resource}{instrum_type}/{instrum}"),
            ocm.instrumentOfScore,
            URIRef(f"{ocm_resource}{score_type}/{score_id}"),
        ))

        # score for song
        knowledge_graph.add((
            URIRef(f"{ocm_resource.Song}/{song_id}"),
            ocm.hasScore,
            URIRef(f"{ocm_resource}{score_type}/{score_id}"),
        ))

        # score for musical creation
        knowledge_graph.add((
            URIRef(f"{ocm_resource.MusicWriting}/{music_creation_id}"),
            ocm.createsComposition,
            URIRef(f"{ocm_resource}{score_type}/{score_id}"),
        ))

        if performer_id.strip() != "":
            # create performer
            knowledge_graph.add((
                URIRef(f"{ocm_resource}{performer_type}/{performer_id}"),
                RDF.type,
                URIRef(f"{ocm}{performer_type}")
            ))

            # add performer name
            knowledge_graph.add((
                URIRef(f"{ocm_resource}{performer_type}/{performer_id}"),
                ocm.hasName,
                Literal(performer_name)
            ))

            # add performer name
            knowledge_graph.add((
                URIRef(f"{ocm_resource}{performer_type}/{performer_id}"),
                RDFS.label,
                Literal(performer_name)
            ))

            # add performer name
            knowledge_graph.add((
                URIRef(f"{ocm_resource}{performer_type}/{performer_id}"),
                RDFS.label,
                Literal(performer_name)
            ))

            # performer executes score
            knowledge_graph.add((
                URIRef(f"{ocm_resource}{performer_type}/{performer_id}"),
                ocm.performsScore,
                URIRef(f"{ocm_resource}{score_type}/{score_id}")
            ))

            # performer plays instrument
            knowledge_graph.add((
                URIRef(f"{ocm_resource}{performer_type}/{performer_id}"),
                ocm.playsInstrument,
                URIRef(f"{ocm_resource}{instrum_type}/{instrum}")
            ))

            # performance involve performer
            knowledge_graph.add((
                URIRef(f"{ocm_resource}{performer_type}/{performer_id}"),
                ocm.performsAt,
                URIRef(f"{ocm_resource.MusicalPerformance}/{performance_id}"),
            ))

######## ALIGNMENT ########

print("########## ONTOLOGY ALIGNMENT ##########")

print("Aligning ontologies...")
alignments = pd.read_csv('../alignment/alignment.txt', sep=' ', keep_default_na=False)
for id, row in tqdm(alignments.iterrows(), total=len(alignments)):
    if row.AlignmentProperty == "equivalentClass":
        ontology.add((
            URIRef(row.Source),
            OWL.equivalentClass,
            URIRef(row.Target)
        ))
    else:
        ontology.add((
            URIRef(row.Source),
            RDFS.subClassOf,
            URIRef(row.Target)
        ))

########## ENTITY LINKING ##########
print("########## ENTITY LINKING ##########")

print("Linking entities on DBpedia...")
f = open('../alignment/linking.txt')
for row in tqdm(f.readlines()):
    source, target, score = row.split('\t')
    # owl:sameAs
    knowledge_graph.add((
        URIRef(source[1:-1]),   # remove < and >
        OWL.sameAs,
        URIRef(target[1:-1])    # remove < and >
    ))

final_graph = ontology + knowledge_graph
final_graph.bind("ocm", ocm)
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
