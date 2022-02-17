import subprocess
import bs4
import pandas as pd
import re


# define cross-composer and cross-era dataset link
CROSS_COMPOSER_URL = "https://www.audiolabs-erlangen.de/content/resources/MIR/cross-comp/cross-composer_annotations.csv"
CROSS_ERA_URL = "https://www.audiolabs-erlangen.de/content/resources/MIR/cross-era/cross-era_annotations.csv"


# Define function to extract table from the queried operadatabase page
def scrape_opera_database(category: str = "operas") -> pd.DataFrame:
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
        return df

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
        return df

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
        return df

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
        return df

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
        return df
    else:
        raise Exception(f"Category{category} does not exist, try another one.")


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
