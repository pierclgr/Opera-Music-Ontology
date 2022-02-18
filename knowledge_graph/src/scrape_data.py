import os.path
import subprocess
import bs4
import pandas as pd
import re
import wget

# define cross-composer and cross-era dataset links
CROSS_COMPOSER_URL = "https://www.audiolabs-erlangen.de/content/resources/MIR/cross-comp/cross-composer_annotations.csv"
CROSS_ERA_URL = "https://www.audiolabs-erlangen.de/content/resources/MIR/cross-era/cross-era_annotations.csv"

# define cross-composer and cross-era dataset paths
CROSS_COMPOSER_PATH = "../data/cross_composer.csv"
CROSS_ERA_PATH = "../data/cross_era.csv"


# Define function to extract table from the queried operadatabase page
def scrape_opera_database(category: str = "operas") -> pd.DataFrame:

    csv_file_path = f"../data/operadb_{category}.csv"

    # check if file exists
    if os.path.isfile(csv_file_path):
        df = pd.read_csv(csv_file_path)
    else:
        print(f"Downloading Opera Database {category.replace('_', ' ').title()} from the web, please wait...")
        # define url to query and table id to extract based on the chosen category
        if category == "operas":
            table_id = "operadatatable"
            query_page = "https://theoperadatabase.com/operas.php"

            # query chosen webpage to obtain html code
            html_code = subprocess.check_output(f'curl {query_page}', shell=True)
            soup = bs4.BeautifulSoup(html_code, features="html.parser")
            table = soup.find("table", {"id": table_id})

            # create matrix corresponding to table
            # create empty row list
            df_rows = []
            # for each tr row
            for row in table.find_all("tr"):
                # create empty columns list
                df_cols = []
                # if current row is in table head, create headers row
                if row.parent.name == 'thead':
                    for cell in row.find_all("th"):
                        cell_text = cell.get_text()
                        if cell_text == 'Premiere':
                            df_cols.append('Date')
                        elif cell_text == 'IMSLP':
                            df_cols.append('Sheet')
                        elif cell_text == "Operabase":
                            pass
                        else:
                            df_cols.append(cell_text)
                    # add new headers
                    df_cols = df_cols + ['Composer lifetime', 'Composer nationality', 'Composer Wikipedia']
                # otherwise, it is not table head so it contains data
                else:
                    # extract row content
                    row_content = row.find_all("td")

                    # extract data from rows
                    composer = row_content[0]
                    opera = row_content[1]
                    date = row_content[2]
                    language = row_content[3]
                    sheet = row_content[4]
                    synopsis = row_content[5]
                    wikipedia = row_content[6]
                    libretto = row_content[7]

                    # remove a tag from sheet link
                    for a_tag in sheet.find_all("a"):
                        # get href link and replace its parent content with the link itself
                        href = a_tag.get('href')
                        sheet.clear()
                        sheet.string = href

                    # remove a tag from synopsis link
                    for a_tag in synopsis.find_all("a"):
                        # get href link and replace its parent content with the link itself
                        href = a_tag.get('href')
                        synopsis.clear()
                        synopsis.string = href

                    # remove a tag from wikipedia link
                    for a_tag in wikipedia.find_all("a"):
                        # get href link and replace its parent content with the link itself
                        href = a_tag.get('href')
                        wikipedia.clear()
                        wikipedia.string = href

                    # remove a tag from libretto link
                    for a_tag in libretto.find_all("a"):
                        # get href link and replace its parent content with the link itself
                        href = a_tag.get('href')
                        libretto.clear()
                        libretto.string = href

                    # extract composer lifetime, nationality and wikipedia link
                    composer_nationality, composer_lifetime = extract_nationality_lifetime(composer, category)
                    composer_wikipedia_link = extract_link(composer)

                    # append extracted information to the end of the row
                    df_cols = [composer.get_text(), opera.get_text(), date.get_text(),
                               language.get_text(),
                               sheet.get_text(), synopsis.get_text(), wikipedia.get_text(), libretto.get_text(),
                               composer_lifetime, composer_nationality, composer_wikipedia_link]

                df_rows.append(df_cols)

            # create dataframe from matrix and return
            df = pd.DataFrame(df_rows[1:], columns=df_rows[0])

        elif category == "zarzuela":
            table_id = "zarzueladatatable"
            query_page = "https://theoperadatabase.com/zarzuela.php"

            # query chosen webpage to obtain html code
            html_code = subprocess.check_output(f'curl {query_page}', shell=True)
            soup = bs4.BeautifulSoup(html_code, features="html.parser")
            table = soup.find("table", {"id": table_id})

            # create matrix corresponding to table
            # create empty row list
            df_rows = []
            # for each tr row
            for row in table.find_all("tr"):
                # create empty columns list
                df_cols = []
                # if current row is in table head, create headers row
                if row.parent.name == 'thead':
                    for cell in row.find_all("th"):
                        cell_text = cell.get_text()
                        if cell_text == 'Score':
                            df_cols.append('Sheet')
                        elif cell_text == 'Zarzuela':
                            df_cols.append('Opera')
                        else:
                            df_cols.append(cell_text)
                    # add new headers
                    df_cols = df_cols + ['Composer lifetime', 'Composer nationality', 'Composer Wikipedia']
                # otherwise, it is not table head so it contains data
                else:
                    # extract row content
                    row_content = row.find_all("td")

                    # fix composer tag closigng </td>
                    string_composer_tag = str(row_content[0])
                    string_composer_tag = f"{string_composer_tag[0:string_composer_tag.find('<td>', 2)]}</td>"
                    temp_soup = bs4.BeautifulSoup(string_composer_tag, 'html.parser')
                    row_content[0] = temp_soup.find_all('td')[0]

                    # extract data from rows
                    composer = row_content[0]
                    opera = row_content[1]
                    date = row_content[2]
                    language = row_content[3]
                    sheet = row_content[4]
                    synopsis = row_content[5]
                    wikipedia = row_content[6]
                    libretto = row_content[7]

                    # remove a tag from sheet link
                    for a_tag in sheet.find_all("a"):
                        # get href link and replace its parent content with the link itself
                        href = a_tag.get('href')
                        sheet.clear()
                        sheet.string = href

                    # remove a tag from synopsis link
                    for a_tag in synopsis.find_all("a"):
                        # get href link and replace its parent content with the link itself
                        href = a_tag.get('href')
                        synopsis.clear()
                        synopsis.string = href

                    # remove a tag from wikipedia link
                    for a_tag in wikipedia.find_all("a"):
                        # get href link and replace its parent content with the link itself
                        href = a_tag.get('href')
                        wikipedia.clear()
                        wikipedia.string = href

                    # remove a tag from libretto link
                    for a_tag in libretto.find_all("a"):
                        # get href link and replace its parent content with the link itself
                        href = a_tag.get('href')
                        libretto.clear()
                        libretto.string = href

                    # extract composer lifetime, nationality and wikipedia link
                    composer_nationality, composer_lifetime = extract_nationality_lifetime(composer, category)
                    composer_wikipedia_link = extract_link(composer)

                    # append extracted information to the end of the row
                    df_cols = [composer.get_text().replace("fullname", "?"), opera.get_text(), date.get_text(),
                               language.get_text(),
                               sheet.get_text(), synopsis.get_text(), wikipedia.get_text(), libretto.get_text(),
                               composer_lifetime, composer_nationality, composer_wikipedia_link]

                df_rows.append(df_cols)

            # create dataframe from matrix and return
            df = pd.DataFrame(df_rows[1:], columns=df_rows[0])

        elif category == "arias":
            table_id = "ariadatatable"
            query_page = "https://theoperadatabase.com/arias.php"

            # query chosen webpage to obtain html code
            html_code = subprocess.check_output(f'curl {query_page}', shell=True)
            soup = bs4.BeautifulSoup(html_code, features="html.parser")
            table = soup.find("table", {"id": table_id})

            # create matrix corresponding to table
            # create empty row list
            df_rows = []
            # for each tr row
            for row in table.find_all("tr"):
                # create empty columns list
                df_cols = []
                # if current row is in table head, create headers row
                if row.parent.name == 'thead':
                    for cell in row.find_all("th"):
                        cell_text = cell.get_text()
                        if cell_text == 'PDF':
                            df_cols.append('Sheet')
                        elif cell_text == 'Voice/Fach':
                            df_cols.append('Voice')
                        else:
                            df_cols.append(cell_text)
                    # add new headers
                    df_cols = df_cols + ['Composer lifetime', 'Composer nationality', 'Composer Wikipedia',
                                         'Opera link']
                # otherwise, it is not table head so it contains data
                else:
                    # extract row content
                    row_content = row.find_all("td")

                    # for each cell of the row
                    for cell in row_content:
                        # remove pdf buttons if available and replace them with their link
                        for a_tag in cell.find_all("a", {"class": "pdfbutton"}):
                            # get href link and replace its parent content with the link itself
                            href = a_tag.get('href')
                            cell.clear()
                            cell.string = href
                        # append cell value to current row
                        df_cols.append(cell.get_text())

                    # extract composer lifetime, nationality and wikipedia link
                    composer = row_content[1]
                    composer_nationality, composer_lifetime = extract_nationality_lifetime(composer, category)
                    composer_wikipedia_link = extract_link(composer)

                    # extract album wikipedia link if available
                    opera = row_content[2]
                    opera_link = extract_link(opera)

                    # append extracted information to the end of the row
                    df_cols = df_cols + [composer_lifetime, composer_nationality, composer_wikipedia_link, opera_link]

                df_rows.append(df_cols)

            # create dataframe from matrix and return
            df = pd.DataFrame(df_rows[1:], columns=df_rows[0])

        elif category == "zarzuela_arias":
            table_id = "zarzuelaariadatatable"
            query_page = "https://theoperadatabase.com/zarzuelaarias.php"

            # query chosen webpage to obtain html code
            html_code = subprocess.check_output(f'curl {query_page}', shell=True)
            soup = bs4.BeautifulSoup(html_code, features="html.parser")
            table = soup.find("table", {"id": table_id})

            # create matrix corresponding to table
            # create empty row list
            df_rows = []
            # for each tr row
            for row in table.find_all("tr"):
                # create empty columns list
                df_cols = []
                # if current row is in table head, create headers row
                if row.parent.name == 'thead':
                    for cell in row.find_all("th"):
                        cell_text = cell.get_text()
                        if cell_text == 'Composer(s)':
                            df_cols.append('Composer')
                        elif cell_text == 'Zarzuela':
                            df_cols.append('Opera')
                        elif cell_text == 'PDF':
                            df_cols.append('Sheet')
                        else:
                            df_cols.append(cell_text)
                    # add new headers
                    df_cols = df_cols + ['Composer lifetime', 'Composer nationality', 'Composer Wikipedia']
                # otherwise, it is not table head so it contains data
                else:
                    # extract row content
                    row_content = row.find_all("td")

                    # fix composer tag closigng </td>
                    string_composer_tag = str(row_content[1])
                    string_composer_tag = f"{string_composer_tag[0:string_composer_tag.find('<td>', 2)]}</td>"
                    temp_soup = bs4.BeautifulSoup(string_composer_tag, 'html.parser')
                    row_content[1] = temp_soup.find_all('td')[0]

                    # for each cell of the row
                    for cell in row_content:
                        # remove pdf buttons if available and replace them with their link
                        for a_tag in cell.find_all("a", {"class": "pdfbutton"}):
                            # get href link and replace its parent content with the link itself
                            href = a_tag.get('href')
                            cell.clear()
                            cell.string = href
                        # append cell value to current row
                        df_cols.append(cell.get_text())

                    # extract composer lifetime, nationality and wikipedia link
                    composer = row_content[1]
                    composer_nationality, composer_lifetime = extract_nationality_lifetime(composer, category)
                    composer_wikipedia_link = extract_link(composer)

                    # append extracted information to the end of the row
                    df_cols = df_cols + [composer_lifetime, composer_nationality, composer_wikipedia_link]

                df_rows.append(df_cols)

            # create dataframe from matrix and return
            df = pd.DataFrame(df_rows[1:-1], columns=df_rows[0])

        elif category == "art_songs":
            table_id = "songdatatable"
            query_page = "https://theoperadatabase.com/songs.php"

            # query chosen webpage to obtain html code
            html_code = subprocess.check_output(f'curl {query_page}', shell=True)
            soup = bs4.BeautifulSoup(html_code, features="html.parser")
            table = soup.find("table", {"id": table_id})

            # create matrix corresponding to table
            # create empty row list
            df_rows = []
            # for each tr row
            for row in table.find_all("tr"):
                # create empty columns list
                df_cols = []
                # if current row is in table head, create headers row
                if row.parent.name == 'thead':
                    for cell in row.find_all("th"):
                        cell_text = cell.get_text()
                        if cell_text == 'Cycle':
                            df_cols.append('Album')
                        elif cell_text == 'Low PDF':
                            df_cols.append('Low Sheet')
                        elif cell_text == 'Medium PDF':
                            df_cols.append('Medium Sheet')
                        elif cell_text == 'High PDF':
                            df_cols.append('High Sheet')
                        else:
                            df_cols.append(cell_text)
                    # add new headers
                    df_cols = df_cols + ['Composer lifetime', 'Composer nationality', 'Composer Wikipedia',
                                         'Album wikipedia']
                # otherwise, it is not table head so it contains data
                else:
                    # extract row content
                    row_content = row.find_all("td")
                    # for each cell of the row
                    for cell in row_content:
                        # remove pdf buttons if available and replace them with their link
                        for a_tag in cell.find_all("a", {"class": "pdfbutton"}):
                            # get href link and replace its parent content with the link itself
                            href = a_tag.get('href')
                            cell.clear()
                            cell.string = href
                        # append cell value to current row
                        df_cols.append(cell.get_text())

                    # extract objects that may have popup content
                    album = row_content[1]
                    composer = row_content[2]

                    # extract album wikipedia link if available
                    album_wikipedia_link = extract_link(album)

                    # extract composer lifetime, nationality and wikipedia link
                    composer_nationality, composer_lifetime = extract_nationality_lifetime(composer, category)
                    composer_wikipedia_link = extract_link(composer)

                    # append extracted information to the end of the row
                    df_cols = df_cols + [composer_lifetime, composer_nationality, composer_wikipedia_link,
                                         album_wikipedia_link]

                df_rows.append(df_cols)

            # create dataframe from matrix and return
            df = pd.DataFrame(df_rows[1:], columns=df_rows[0])
        else:
            raise Exception(f"Category{category} does not exist, try another one.")

        # save downloaded dataset
        df.to_csv(csv_file_path)
        return df


# define function to extract link from a <td> tag of class popover-content
def extract_link(cell):
    info_link = ""
    link = cell.find_all("a")
    i = 0
    for composer in link:
        if i > 0:
            info_link += ", "
        # extract the wikipedia link
        for info in re.findall(r'<a[^>]* href="([^"]*)"', composer.get("data-content")):
            info_link += info
            break
        i += 1
    return info_link


# define function to extract lifetime and nationality of a composer
def extract_nationality_lifetime(cell, category):
    popover = cell.find_all("a")
    nationality = ''
    lifetime = ''
    i = 0
    for a_tag in popover:
        if i > 0:
            nationality += ", "
            lifetime += ", "
        a_tag_data_content = a_tag.get("data-content").replace("<p>", ",").split(",")
        if category == "zarzuela_arias" or category == "zarzuela":
            a_tag_data_content.remove('')
            if re.match(".*[\d]*[\s]*-[\s]*[\d]*.*", a_tag_data_content[0]):
                nationality += ""
                lifetime += a_tag_data_content[0].replace(" ", "")
            elif len(re.findall(r'<a[^>]* href="([^"]*)"', a_tag_data_content[0])) > 0:
                nationality += ""
                lifetime += ""
            elif re.search("dates.*", a_tag_data_content[0]):
                nationality += ""
                lifetime += ""
            else:
                nationality += a_tag_data_content[0].split()[0]
                lifetime += a_tag_data_content[1].replace(" ", "")
        elif category == "art_songs" or category == "arias" or category == "operas":
            a_tag_data_content = a_tag_data_content[0].split(":")
            current_nat = a_tag_data_content[0].split()[0]
            if current_nat != "composer":
                nationality += current_nat
            lifetime += a_tag_data_content[1].replace(" ", "")
        else:
            raise Exception(f"Category{category} does not exist, try another one.")
        i += 1
    return nationality, lifetime


# define function to download file
def download_file(url, path):
    print("Downloading dataset from the web, please wait...")
    wget.download(url, out=path)


# define function to scrape cross-composer dataset from web
def scrape_cross_composer() -> pd.DataFrame:
    if not os.path.isfile(CROSS_COMPOSER_PATH):
        download_file(CROSS_COMPOSER_URL, CROSS_COMPOSER_PATH)
        cross_composer = pd.read_csv(CROSS_COMPOSER_PATH)

        # fix double composers
        mask = cross_composer['Artist_filter_no'] == 15
        brahms_15 = cross_composer.loc[mask].copy()
        brahms_15.Album = brahms_15.Album.str.split(" / ", expand=True)[1]
        cross_composer[mask] = brahms_15

        mask = cross_composer['Artist_filter_no'] == 12
        brahms_12 = cross_composer.loc[mask].copy()
        composer_regex = re.compile(r'[A-Z ;]+\.: [^/]+/[A-Z ;]+\.: [^/]+')
        brahms_12.Album = brahms_12.Album.apply(lambda x: x.split(" / ")[0] if composer_regex.match(x) else x)
        cross_composer[mask] = brahms_12

        mask = cross_composer.Artist_filter_no == 36
        mendelssohn_36 = cross_composer.loc[mask].copy()
        mendelssohn_36.Album = mendelssohn_36.Album.str.split(" / ", expand=True)[0]
        cross_composer[mask] = mendelssohn_36

        # remove composer name from album name column
        cross_composer.Album = cross_composer.Album.apply(
            lambda x: re.sub(r"[A-Z/ ]+(;[A-Za-z. /\-]+)*: *", "", x).strip("'").replace("''", "'"))

        # refactor filename
        cross_composer.Filename = cross_composer.apply(
            lambda x: x['Filename'].replace(f"{x['CrossComp-ID']}_{x['Class']}_", "")
                .replace(".mp3", "").replace("_", " ").title(), axis=1)

        # replace iii* pattern with III* in filename
        cross_composer.Filename = cross_composer.Filename.apply(
            lambda x: re.sub(r"[Ii][Ii]+", upper_repl, x))

        # refactor instruments and performers
        cross_composer['Conductor'] = ""

        # define name surname dictionary
        name_dict = {
            "Muller-Bruhl": "Müller-Brühl, Helmut",
            "Standovsky": "Stankovsky, Robert",
            "Chang": "Chang, Hae Won",
            "Jando": "Jandó, Jenő",
            "Ruebsam": "Rübsam, Wolfgang",
            "Mallon": "Mallon, Kevin",
            "Dawes": "Dawes, Christopher",
            "Gallagher": "Gallagher, Kevin R.",
            "Demmler": "Demmler, Jürgen",
            "Grabinger": "Grabinger, Peter",
            "Tillier": "Tillier, Markus",
            "Kostelnik": "Kostelnik, Steve",
            "Kodaly Quartet": "Kodály Quartet",
            "Grunzenhauser": "Gunzenhauser, Stephen",
            "Gunzenhauser": "Gunzenhauser, Stephen",
            "Drahos": "Drahos, Béla",
            "Nicolaus Esterhazy Sinfonia": "Nicolaus Esterházy Sinfonia",
            "Wit": "Wit, Antoni",
            "Biret": "Biret, Idil",
            "Onczay": "Onczay, Csaba",
            "Takacs": "Takacs, Tamara",
            "Kaiser": "Kaiser, Karl",
            "Donose": "Donose, Ruxandra",
            "Fink": "Fink, Manfred",
            "Otelli": "Otelli, Claudio",
            "Papian": "Papian, Hasmik",
            "Balogh": "Balogh, József",
            "Tebenikhin": "Tebenikhin, Amir",
            "Nishizaki": "Nishizaki, Takako",
            "Pasquier": "Pasquier, Bruno",
            "Bisengaliev": "Bisengaliev, Marat",
            "Lenehan": "Lenehan, John",
            "Kohn": "Köhn, Christian",
            "Matthies": "Matthies, Silke-Thora",
            "Parkins": "Parkins, Robert",
            "Qian": "Qian, Zhou",
            "Battersby": "Battersby, Edmund",
            "Kosler": "Košler, Zdeněk",
            "Halasz": "Halász, Michael",
            "Kliegel": "Kliegel, Maria",
            "Klochinsky": "Kolchinsky, Camilla",
            "Kaler": "Kaler, Ilya",
            "Peled": "Peled, Amit",
            "Goldstein": "Goldstein, Alon",
            "Kopelman": "Kopelman, Jozef",
            "Goodman": "Goodman, Roy",
            "Pasichnyk": "Pasichnyk, Olga",
            "Pomakov": "Pomakov, Robert",
            "Dixon": "Dixon, Chris",
            "Mields": "Mields, Dorothee",
            "Andersen": "Andersen, Ulrike",
            "Wilde": "Wilde, Mark",
            "Chuckston": "Cuckston, Alan",
            "Ward": "Ward, Nicholas",
            "Camden": "Camden, Anthony",
            "Girdwood": "Girdwood, Julia",
            "Wordsworth": "Wordsworth, Barry",
            "Jean": "Jean, Kenneth",
            "Garcia": "Garcia, Gerald",
            "Seifried": "Seifried, Reinhard",
            "Bramall": "Bramall, Anthony",
            "Dohnanyi": "Dohnányi, Oliver",
            "Frith": "Frith, Benjamin",
            "Chamberlan": "Chamberlan, Jean-Francois",
            "Grauwels": "Grauwels, Marc",
            "Devos": "Devos, Luc",
            "Merscher": "Merscher, Kristin",
            "Stankovsky": "Stankovsky, Robert",
            "Markl": "Märkl, Jun",
            "Elsner": "Elsner, Christian",
            "Erdmann": "Erdmann, Mojca",
            "Ziesak": "Ziesak, Ruth",
            "Sebestyen": "Sebestyén, János",
            "Kyselak": "Kyselák, Ladislav",
            "Dickie": "Dickie, John",
            "Wildner": "Wildner, Johannes",
            "Harden": "Harden, Wolf",
            "Kollar": "Kollár, Zsuzsa",
            "Thompson": "Thompson, Michael",
            "Rowland": "Rowland, Gilbert",
            "Terey-Smith": "Terey-Smith, Mary",
            "Mitchel": "Mitchell, Kenneth",
            "Parry": "Parry, Elizabeth",
            "Laux": "Laux, Stefan",
            "Bastlein": "Bästlein, Ulf",
            "Eisenlohr": "Eisenlohr, Ulrich",
            "Bruns": "Bruns, Martin",
            "Jakobi": "Jakobi, Regina",
            "Volle": "Volle, Michael",
            "Scott": "Scott, Sjon",
            "Trekel": "Trekel, Roman",
            "Eder Quartet": "Éder Quartet",
            "Scherbakov": "Scherbakov, Konstantin",
            "Petrenko": "Petrenko, Vasily",
            "Kuchar": "Kuchar, Theodore",
            "Lyndon-Gee": "Lyndon-Gee, Christopher",
            "Houston": "Houstoun, Michael"
        }

        for index, row in cross_composer.iterrows():
            instrumentation = row.Instrumentation
            conductor = row.Conductor
            roles = row.Performer.split("; ")
            instrumentation = instrumentation.split("; ")
            performer = roles
            if row.Artist_filter_no == 2:
                performer = [roles[0], roles[2]]
                conductor = roles[1]
                instrumentation.reverse()
            elif row.Artist_filter_no == 5:
                instrumentation.reverse()
                performer = [roles[0]]
                if 2 < len(roles):
                    performer.append(roles[2])
                conductor = roles[1]
            elif row.Artist_filter_no == 9:
                if len(instrumentation) > 1 and instrumentation[1] == "quartet":
                    performer += performer
            elif row.Artist_filter_no == 1 or row.Artist_filter_no == 10 or row.Artist_filter_no == 11 or \
                    row.Artist_filter_no == 2 or row.Artist_filter_no == 24 or row.Artist_filter_no == 29 \
                    or row.Artist_filter_no == 35 or row.Artist_filter_no == 38 or row.Artist_filter_no == 42 \
                    or row.Artist_filter_no == 55 or row.Artist_filter_no == 57 or row.Artist_filter_no == 66:
                performer = [roles[0]]
                conductor = roles[1]
                if row.Artist_filter_no == 11:
                    if len(instrumentation) > 1:
                        performer.append("Nicolaus Esterházy Chorus")
            elif row.Artist_filter_no == 12:
                if instrumentation[0] == "orchestra":
                    performer = ["Polish National Radio Symphony Orchestra"] + performer
                    conductor = "Wit"
                    instrumentation.append("piano")
            elif row.Artist_filter_no == 16:
                performer = ["Ludwig Quartet", roles[1]]
                instrumentation.append("viola")
            elif row.Artist_filter_no == 19:
                performer = ["Ludwig Quartet"]
            elif row.Artist_filter_no == 25:
                performer = [roles[0]]
                conductor = roles[1].replace(";", "")
            elif row.Artist_filter_no == 13:
                if len(instrumentation) > 3:
                    tail_instrumentation = instrumentation[2:]
                    tail_instrumentation.reverse()
                    instrumentation = [instrumentation[0], "quartet", instrumentation[1]] + tail_instrumentation
                else:
                    instrumentation += ["piano", "cello"]
                performer = [roles[0], roles[0], "Balogh", roles[1], roles[2]]
            elif row.Artist_filter_no == 15 or row.Artist_filter_no == 36 or row.Artist_filter_no == 44 \
                    or row.Artist_filter_no == 49:
                performer = [roles[0], roles[2]]
                conductor = roles[1]
            elif row.Artist_filter_no == 17:
                performer = [""] + performer
                instrumentation += ["violin", "piano"]
            elif row.Artist_filter_no == 51:
                performer = [""] + performer
            elif row.Artist_filter_no == 22:
                performer = [""] + performer
            elif row.Artist_filter_no == 18:
                if len(instrumentation) > 1:
                    performer = ["", ""] + performer
                    instrumentation += ["piano", "piano"]
                else:
                    if instrumentation[0] == "piano":
                        instrumentation += instrumentation
                    else:
                        performer = [""] + performer
                        instrumentation += ["piano", "piano"]
            elif row.Artist_filter_no == 26:
                if instrumentation[1].lower() == "cello":
                    performer = [roles[0], roles[2]]
                    conductor = roles[1]
                else:
                    performer = [roles[0], roles[1]]
                    conductor = roles[2]
            elif row.Artist_filter_no == 27:
                performer = [roles[0], roles[1]]
                conductor = roles[2]
            elif row.Artist_filter_no == 28:
                performer = [""] + performer
                tail_instrumentation = instrumentation[1:]
                tail_instrumentation.reverse()
                instrumentation = [instrumentation[0]] + tail_instrumentation
            elif row.Artist_filter_no == 30:
                instrumentation = ["orchestra"] + instrumentation
            elif row.Artist_filter_no == 31:
                instrumentation.reverse()
                instrumentation = ["orchestra"] + instrumentation
                performer = [roles[0]] + roles[2:]
                conductor = roles[1]
            elif row.Artist_filter_no == 32:
                performer = [roles[1]]
                performer += [roles[0]]
                performer += [roles[3], roles[4], roles[2].replace(" ", ""), roles[5]]
                instrumentation = ["ensemble"] + instrumentation
            elif row.Artist_filter_no == 34:
                instrumentation += [instrumentation[1]]
                conductor = "Ward"
                performer = ["City of London Sinfonia"] + performer
            elif row.Artist_filter_no == 39:
                performer = [roles[0]]
                conductor = "; ".join(roles[1:])
            elif row.Artist_filter_no == 41:
                performer = ["", roles[0], roles[3], roles[2]]
                conductor = roles[1]
            elif row.Artist_filter_no == 43:
                performer = [""] + roles
            elif row.Artist_filter_no == 45:
                conductor = roles[2]
                performer = roles[0:2] + roles[3:]
                instrumentation = instrumentation[0:2] + [instrumentation[-1]] + [instrumentation[-2]] + [
                    instrumentation[-2]]
            elif row.Artist_filter_no == 48:
                conductor = roles[1]
                performer = [roles[0], roles[3], roles[2]]
            elif row.Artist_filter_no == 52:
                instrumentation += instrumentation
            elif row.Artist_filter_no == 56:
                performer = roles[1:]
                performer += [roles[0]]
                performer = [""] + performer
            elif row.Artist_filter_no == 58 or row.Artist_filter_no == 59 or row.Artist_filter_no == 60:
                performer.reverse()
            elif row.Artist_filter_no == 61:
                if len(instrumentation) < 3:
                    instrumentation += ["horn"]
                performer = [roles[0], roles[2], roles[1]]
            elif row.Artist_filter_no == 65:
                performer = [roles[0]]
                conductor = "Petrenko"
            elif row.Artist_filter_no == 67:
                performer = roles[0:2]
                conductor = roles[2]
            elif row.Artist_filter_no == 68:
                performer = roles[0:2]
                conductor = roles[2]

            diff = len(performer) - len(instrumentation)
            if diff < 0:
                [performer.append("") for _ in range(abs(diff))]
            elif diff > 0:
                [instrumentation.append("") for _ in range(abs(diff))]

            conductor = conductor.split("; ")
            conductor = [name_dict[k.strip(" ")].strip(" ") if k.strip(" ") in name_dict else k.strip(" ") for k in
                         conductor]
            performer = [name_dict[k.strip(" ")].strip(" ") if k.strip(" ") in name_dict else k.strip(" ") for k in
                         performer]

            cross_composer.at[index, 'Instrumentation'] = " ".join(instrumentation).title().replace(" ", "; ")
            cross_composer.at[index, 'Conductor'] = "; ".join(conductor)
            cross_composer.at[index, 'Performer'] = "; ".join(performer)

        cross_composer.to_csv(CROSS_COMPOSER_PATH)
    else:
        cross_composer = pd.read_csv(CROSS_COMPOSER_PATH)

    return cross_composer


# define function to scrape cross-era dataset from web
def scrape_cross_era() -> pd.DataFrame:
    if not os.path.isfile(CROSS_ERA_PATH):
        download_file(CROSS_ERA_URL, CROSS_ERA_PATH)
        cross_era = pd.read_csv(CROSS_ERA_PATH)

        # refactor filename
        cross_era.Filename = cross_era.apply(
            lambda x: x['Filename'].replace(f"{x['CrossEra-ID']}_", "").replace(".mp3", ""), axis=1)

        # fix bad composer names
        for index, row in cross_era.iterrows():
            if re.match(r"^((?!; ).)*$", row.Composer):
                composer = row.CompLifetime
                complifetime = row.Country
                country = row[-1]
                cross_era.at[index, 'Composer'] = composer
                cross_era.at[index, 'CompLifetime'] = complifetime
                cross_era.at[index, 'Country'] = country

            filename = row.Filename
            surname = row.Composer.split('; ')[0]
            name = row.Composer.split("; ")[1]
            filename = filename.title().replace(surname, "")
            filename = filename.title().replace(name, "")
            filename = filename.strip("_")
            filename = filename.split("_-_")

            if len(filename) > 1:
                filename = filename[1]
            else:
                filename = filename[0]

            cross_era.at[index, 'Filename'] = filename.replace("_", " ").replace(name, "")

        # replace iii* pattern with III* in filename
        cross_era.Filename = cross_era.Filename.apply(
            lambda x: re.sub(r"[Ii][Ii]+", upper_repl, x))

        cross_era.drop(columns=cross_era.columns[-1],
                       axis=1,
                       inplace=True)

        cross_era.CompLifetime = cross_era.CompLifetime.apply(lambda x: x.replace("....", ""))
        cross_era.Instrumentation = cross_era.Instrumentation.str.title()
        cross_era.Mode = cross_era.Mode.str.title()
        cross_era.Key = cross_era.Key.str.title()

        cross_era.to_csv(CROSS_ERA_PATH)
    else:
        cross_era = pd.read_csv(CROSS_ERA_PATH)

    return cross_era


# define function to upper matched content
def upper_repl(match):
    return match.group(0).upper()
