# %%
#scrap_editorial_manager.py


# %% [markdown]
# 
# # Extrae los datos de Editorial Manager y los guarda en un dos df
# ### 1. Datos de los artículos en proceso de revisión
# ### 2. Datos de los artículos con de cisión definitiva: aceptados o rechazados

# %%
import requests
from bs4 import BeautifulSoup

username = "mariagps"
user_password = "8Z4vn*!WTP"
role = "editor"
login_data = {"username": username, "password": user_password,  "role": "editor",
              "hdnManuscriptServicesDisplayed" : "false",   'hdnNeedMultipLoginDropdown' : 0,
              'hdnOrcidIsAuthenticated' : 'False', 'hdnOrcidIsDuplicateEmail' : 'False',
              'hdnSsoLoginEnabled' : 'False', 'hdnUseOrcideLogin' : 'True', 'ignoreWarning' : 0,
              'initiateAscoLogin' : 'False', 'orcidAuthenticated' : 0, 'orcidLogin' : 0
 }
#login_data = {"username": username, "password": user_password, "Login": "submit", "role": "editor"}
headers = {
'Accept-Language': 'es-ES,es;q=0.9,en;q=0.8',
'Accept-Encoding': 'gzip, deflate, br',
'Accept': '*/*',
'Connection': 'keep-alive',
'sec-ch-ua' : '"Not?A_Brand";v="8", "Chromium";v="108", "Google Chrome";v="108"',
'sec-ch-ua-mobile' : '?0',
'sec-ch-ua-platform' : '"Windows"',
'DNT' : '1',
'Upgrade-Insecure-Requests' : '1',
'Content-Type' : 'application/x-www-form-urlencoded',
'User-Agent' : 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.190 Safari/537.36',

}

## login 

url = "https://www.editorialmanager.com/nefro/LoginAction.ashx" #este funciona

session = requests.Session()
response = session.get(url)
print(response.status_code)
states = ["__RequestVerificationToken", "Email", "RememberMe"]


post_request = session.post(url,  data=login_data, headers=headers, allow_redirects=True)

#print cookies
cookies = session.cookies.get_dict()
print(cookies)


# %% [markdown]
# Entro en la página, no me muestra la cabecera pero no hay un link de login, así que asumo que estoy logueado. Entro ahora en en Menú ppal

# %%
#call manin menu and save html
url = 'https://www.editorialmanager.com/nefro/manuscript_status.asp'
response = session.get(url)

response

# %% [markdown]
# Hago login en la web pero en la página de autor. Cambio a editor.

# %%
url = "https://www.editorialmanager.com/nefro/manuscript_status.asp"
data = {'role': 'editor',}

#add defaultMenu to cookies: defaultMenu=0; Path=/nefro/; Domain=editorialmanager.com; Secure;
cookies['defaultMenu'] = '0'
cookies['CurrentLang'] = 'es-ES'
cookies['Path'] = '/nefro/'
cookies['Domain'] = 'editorialmanager.com'


headers = {
    'Accept': '*/*',
    'Accept-Encoding': 'gzip, deflate, br',
    'Connection': 'keep-alive',
    #'Content-Type': 'application/x-www-form-urlencoded',
    #add the charset to the content type
    'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
    #add the cookie from the variable cookies
    'Cookie': 'CurrentLang=es-ES; EMSessionID='+cookies['EMSessionID'],
}

response = session.post(url, data=data, headers=headers, cookies=cookies, allow_redirects=True)
print(response.status_code)

# %% [markdown]
# Entro en la página de Manuscritos Asignados

# %%
#manuscritos asignados
url = 'https://www.editorialmanager.com/nefro/AllAssignedSubmissions.aspx'

response = session.post(url, data=data, headers=headers, cookies=cookies, allow_redirects=True)
print(response.status_code)

body = response.text

import re

pattern = re.compile(r'<td class=\'  \' style=\'vertical-align: middle;;\'>.*?</td>')
matches = pattern.findall(body)

if matches:
    print("Descargados correctamente", len(matches), 'manuscritos asignados')

# %% [markdown]
# Scrap del html de manuscritos asignados.

# %%
#create a dataframe called df_Asignados with the columns: numero_manuscrito, tipo_articulo, titulo, autor, fecha_inicial, fecha_estado, estado_actual, editor, estado_evaluacion, decision_editor
import pandas as pd
df_asignados = pd.DataFrame(columns=['numero_manuscrito', 'tipo_articulo', 'titulo', 'autor', 'fecha_inicial', 
                'fecha_estado', 'estado_actual', 'editor', 'estado_evaluacion', 'decision_editor', 'Completo', 'Aceptado', 'Invitado – Sin Respuesta', 'Rechazado', 'Tarde', 'data_identity'])


# %%
#function that find all the rs-headerRow elements
def find_estado_evaluacion(estado_ev_test, id):
    estado_evaluacion_elemento = []
    soup = BeautifulSoup(estado_ev_test, 'html.parser')
    #print('soup',soup.prettify())

    rows = soup.select('.reviewerHoverDetails .rs-headerRow')
    for row in rows:
        count = row.select_one('.rs-countCell span').text
        detail = row.select_one('.rs-detailCell span').text
        #print(count, detail)
        #append the detail and count to the list estado_evaluacion_elemento
        estado_evaluacion_elemento.append(detail)
        estado_evaluacion_elemento.append(count)
        # add the count to the dataframe in the column detail
        df_asignados.loc[id, detail] = count
    return



# %%
#extract the values from the matches
for i in range(len(matches)):
    pattern = re.compile(r'<td class=\'  \' style=\'vertical-align: middle;;\'>')
    values = pattern.split(matches[i])
    #remove the first element because it is empty
    values.pop(0)
    #print(values[1])
    for j in range (len(values)):
        #print(j, values[j])
        #Titulo and autor are in the same field. If the value is the titulo, split in two and save in the corresponding column
        if j == 2:
            #split in two the string by <td class='  ' style='vertical-align: middle;text-align: center;'> 
            pattern = re.compile(r'<td class=\'  \' style=\'vertical-align: middle;text-align: center;\'>')
            title_author = pattern.split(values[j])
            #print(title_author)
            #store in the corresponding column
            df_asignados.loc[i, 'titulo'] = title_author[0]
            df_asignados.loc[i, 'autor'] = title_author[1]

        else:
            #if the column is >2, add 1 to the column number
            if j > 2:
                df_asignados.loc[i, df_asignados.columns[j+1]] = values[j]
            else:

                df_asignados.loc[i, df_asignados.columns[j]] = values[j] 

    #expand estado_evaluacion to columns: doc_id, Completo, Aceptado, Invitado, Rechazado, Tarde
    estado_evaluacion = df_asignados.loc[i, 'estado_evaluacion']
    #print(estado_evaluacion)
    if estado_evaluacion != '':
        find_estado_evaluacion(estado_evaluacion, i)
        
    #extract decision_editor
    decision_editor = df_asignados.loc[i, 'decision_editor']
    #print(decision_editor)
    try:
        #extract link text from the decision_editor_test
        soup_link = BeautifulSoup(decision_editor, 'html.parser')
        link = soup_link.find('a').text
        #print(link)
        #add the link to the dataframe
        df_asignados.loc[i, 'decision_editor'] = link
    except:
        df_asignados.loc[i, 'decision_editor'] = ""

    #in body, we have the data-identity value inside:
    # The lines are in id='fr***' data-identity='****' data-rowindex
    #find the lines with the data-identity value
    pattern = re.compile(r'id=\'fr[0-9]+\' data-identity=\'[0-9]+\' data-rowindex=\'[0-9]+\'')
    matches_data_identity = pattern.findall(body)

    #extract the data-identity value from data-identity='****'. Keep just the numbers between the single quotes
    data_identity = re.findall(r'data-identity=\'([0-9]+)\'', matches_data_identity[i])[0]
    #print( data_identity)
    #store the data-identity in the dataframe
    df_asignados.loc[i, 'data_identity'] = data_identity

#df_asignados.head()


# %%
#remove the column estado_evaluacion
df_asignados.drop('estado_evaluacion', axis=1, inplace=True)
#change the names of the columns Completo, Aceptado, Invitado – Sin Respuesta, Rechazado, Tarde to est_ev_completo, est_ev_aceptado, est_ev_invitado, est_ev_rechazado, est_ev_tarde
df_asignados.rename(columns={'Completo': 'est_ev_completo', 'Aceptado': 'est_ev_aceptado', 'Invitado – Sin Respuesta': 'est_ev_invitado', 'Rechazado': 'est_ev_rechazado', 'Tarde': 'est_ev_tarde'}, inplace=True)
#convert NaN to 0
df_asignados.fillna(0, inplace=True)

# %%
#df_asignados.head()

# %% [markdown]
# # Scrap de manuscritos en proceso de revisión

# %%
#set the data to be sent to the server and ask for 250 rows instead of 25

data = {
    "ClientSettings": {
    "GridSettings": {
        "CPI": 0,
        "DSC": {
            "SE": "InitialDateSubmitted",
            "SD": 1
        },
        "SC": {
            "SE": "RevisionDueDate",
            "SD": 1
        },
        "DPS": 25,
        "PS": 250,
        "O": 3,
    }
    },
}


# %%
#call the page 
#manuscritos en proceso
url_revision = 'https://www.editorialmanager.com/nefro/SubmissionsOutForRevision.aspx'


response_revision = session.post(url_revision, data=data, headers=headers, cookies=cookies, allow_redirects=True)
print(response_revision.status_code)

body_revision = response_revision.text


# %% [markdown]
# Scrap del html de la tabla de manuscritos en proceso de revisión

# %%
#find from id='nfr to <td class='colresize-cell  ' style=';'></td></tr>
starting_with = 'id=\'nfr'
ending_with = '<td class=\'colresize-cell  \' style=\';\'></td></tr>'

#define the pattern with the starting and ending strings
pattern = re.compile(rf'{starting_with}.*?{ending_with}', re.DOTALL)

#find the matches
matches_revision = pattern.findall(body_revision)

print(len(matches_revision))


# %%
df_revision = pd.DataFrame(columns=['numero_manuscrito', 'tipo_articulo', 'titulo', 'autor', 'email', 'fecha_inicial', 
                'fecha_vencimiento', 'fecha_estado',  'estado_actual', 'decision_editor', 'data_identity'])


# %%
#extract the values from the matches
for i in range(len(matches_revision)):
    pattern = re.compile(r'<td class=\'  \' style=\'vertical-align: middle;;\'>')
    values = pattern.split(matches_revision[i])

    #remove the &#13;&#10;&#13;&#10; characters and 
    values = [re.sub(r'&#13;', '', value) for value in values]
    values = [re.sub(r'&#10;', '', value) for value in values]
    # change &#160; to "\n"
    values = [re.sub(r'&#160;', '\n', value) for value in values]


    #extract the data-identity value from data-identity='****'. Keep just the numbers between the single quotes
    data_identity = re.findall(r'data-identity=\'([0-9]+)\'', matches_revision[i])[0]
    #print( data_identity)
    #store the data-identity in the dataframe
    df_revision.loc[i, 'data_identity'] = data_identity

    #save the numero_manuscrito in the dataframe
    df_revision.loc[i, 'numero_manuscrito'] = values[1]
    #save the tipo_articulo in the dataframe
    df_revision.loc[i, 'tipo_articulo'] = values[2]
    #save the titulo and the autor in the dataframe. 
    #Titulo and autor are in the same field. 
    #split in two the string by <td class='  ' style='vertical-align: middle;text-align: center;'>
    pattern = re.compile(r'<td class=\'  \' style=\'vertical-align: middle;text-align: center;\'>')
    title_author = pattern.split(values[3])
    #save the title in the dataframe
    df_revision.loc[i, 'titulo'] = title_author[0]
    #author is in <a href=\"javascript:showReviewerInfo(13428)\">Andreea Rata </a>
    #extract the author
    author = title_author[1]
    #remove the "\ characters
    author = author.replace('\\"', '') 
    soup = BeautifulSoup(author, 'html.parser')
    author_name = soup.get_text()
    #save the author in the dataframe
    df_revision.loc[i, 'autor'] = author_name

    #extract the email from <span class=\\"email\\" title=\\"
    author_email = soup.find('span', class_='email')["title"]
    #split the string by the semicolon
    author_email = author_email.split(';')
    #print(author_email)
    if len(author_email) > 0:
        df_revision.loc[i, 'email'] = author_email

    #save the fecha_inicial in the dataframe
    df_revision.loc[i, 'fecha_inicial'] = values[4]
    #save the fecha_vencimiento in the dataframe
    df_revision.loc[i, 'fecha_vencimiento'] = values[5]
    #save the fecha_estado in the dataframe
    df_revision.loc[i, 'fecha_estado'] = values[6]
    #save the estado_actual in the dataframe
    df_revision.loc[i, 'estado_actual'] = values[7]
    #get decision_editor 
    decision_editor = values[8]
    soup = BeautifulSoup(decision_editor, 'html.parser')
    link = soup.find('a')
    #get the text from the link
    decision_editor = link.get_text()
    #save the decision_editor in the dataframe
    df_revision.loc[i, 'decision_editor'] = decision_editor

#df_revision.head()
 

# %% [markdown]
# # Junto los dos scrapes en un solo dataframe

# %%
#add the data of the two dataframes df_asignados and df_revision into one dataframe called df_en_proceso. using concat
df_en_proceso = pd.concat([df_asignados, df_revision], ignore_index=True)

#change NaN to ''
df_en_proceso = df_en_proceso.fillna('')

#add two columns: 'fecha_alta' y 'fecha_baja'
df_en_proceso['fecha_alta'] = ''
df_en_proceso['fecha_baja'] = ''

#save to csv
df_en_proceso.to_csv('en_proceso_actual.csv', index=False)

print('en_proceso_actual.csv guardado. ', len(df_en_proceso),'filas  ', len(df_en_proceso.columns),'columnas',)

# %% [markdown]
# # Scrap de decisión definitiva

# %%
#set the data to be sent to the server and ask for 250 rows instead of 25

data = {
    "ClientSettings": {
    "GridSettings": {
        "CPI": 0,
        "DSC": {
            "SE": "InitialDateSubmitted",
            "SD": 1
        },
        "SC": {
            "SE": "StatusDate",
            "SD": 1
        },
        "DPS": 25,
        "PS": 50,
        "O": 1,
    }
    },
}

#En la cabecera "ClientSettings"->"GridSettings"->"DSC"->"SE" tiene el valor "StatusDate" y en 
# "DSC"->"SD" el valor 1, indica que se ordenará los resultados por el campo "StatusDate" en orden ascendente.





# %%
#call the page 
#manuscritos en proceso
url_definitiva = 'https://www.editorialmanager.com/nefro/AllSubmissionsWithFinalDisposition.aspx'


response_definitiva = session.post(url_definitiva, data=data, headers=headers, cookies=cookies, allow_redirects=True)
print(response_definitiva.status_code)

body_definitiva = response_definitiva.text


# %%
#find from id='nfr to <td class='colresize-cell  ' style=';'></td></tr>
starting_with = 'id=\'nfr'
ending_with = '<td class=\'colresize-cell  \' style=\';\'></td></tr>'

#define the pattern with the starting and ending strings
pattern = re.compile(rf'{starting_with}.*?{ending_with}', re.DOTALL)

#find the matches
matches_definitva = pattern.findall(body_definitiva)

print(len(matches_definitva))


# %%
#define a dataframe to store the data
df_definitiva = pd.DataFrame(columns=['numero_manuscrito', 'tipo_articulo', 'titulo', 'autor', 'fecha_inicial', 
                'fecha_estado', 'estado_actual', 'editor', 'estado_evaluacion', 'decision_editor', 'data_identity'])


# %%
for i in range(len(matches_definitva)):
    pattern = re.compile(r'<td class=\'  \' style=\'vertical-align: middle;;\'>')
    values = pattern.split(matches_definitva[i])

    #remove the &#13;&#10;&#13;&#10; characters and 
    values = [re.sub(r'&#13;', '', value) for value in values]
    #remove &#8220;
    values = [re.sub(r'&#8220;', '', value) for value in values]
    #remove &quot;
    values = [re.sub(r'&quot;', '', value) for value in values]

    values = [re.sub(r'&#160;&#10;', ' - ', value) for value in values]
    # change &#160; to "\n"
    values = [re.sub(r'&#160;', ' - ', value) for value in values]
    #change &#10; to line return
    values = [re.sub(r'&#10;', ' - ', value) for value in values]


    #extract the data-identity value from data-identity='****'. Keep just the numbers between the single quotes
    data_identity = re.findall(r'data-identity=\'([0-9]+)\'', matches_definitva[i])[0]
    #print( data_identity)
    #store the data-identity in the dataframe
    df_definitiva.loc[i, 'data_identity'] = data_identity
    
    #save the numero_manuscrito in the dataframe
    df_definitiva.loc[i, 'numero_manuscrito'] = values[1]
    #save the tipo_articulo in the dataframe
    df_definitiva.loc[i, 'tipo_articulo'] = values[2]
    #save the titulo and the autor in the dataframe. 
    #Titulo and autor are in the same field. 
    #split in two the string by <td class='  ' style='vertical-align: middle;text-align: center;'>
    pattern = re.compile(r'<td class=\'  \' style=\'vertical-align: middle;text-align: center;\'>')
    df_definitiva.loc[i, 'titulo'] = pattern.split(values[3])[0]
    #store the autor
    df_definitiva.loc[i, 'autor'] = pattern.split(values[4])[0]
    #save the fecha_inicial in the dataframe
    df_definitiva.loc[i, 'fecha_inicial'] = values[5]
    #save the fecha_estado in the dataframe
    df_definitiva.loc[i, 'fecha_estado'] = values[6]
    #save the estado_actual in the dataframe
    df_definitiva.loc[i, 'estado_actual'] = values[7]
    #save the editor in the dataframe
    df_definitiva.loc[i, 'editor'] = values[8]
    #save the estado_evaluacion in the dataframe
    df_definitiva.loc[i, 'estado_evaluacion'] = values[9]
    #get decision_editor if exists

    decision_editor = values[10]
    #print(decision_editor)
    #get the link from the decision_editor if exists



    soup = BeautifulSoup(decision_editor, 'html.parser')
    link = soup.find('a')
    #save the text from the link if exists
    if link:
        decision_editor = link.get_text()
        #print(decision_editor)
    else:
        decision_editor = ''
        #print(decision_editor)

    df_definitiva.loc[i, 'decision_editor'] = decision_editor




#df_definitiva.head()

# %%
#save to csv
df_definitiva.to_csv('definitiva_actual.csv', index=False)


print('definitiva_actual.csv guardado. ', len(df_definitiva),'filas  ', len(df_definitiva.columns),'columnas',)

# %%



# %%


# %%


# %%


# %%


# %%


# %%


# %%


# %%
df_en_proceso.head()

# %% [markdown]
# # Bajar información de manuscritos asignados individualmente

# %%
# https://www.editorialmanager.com/nefro/doc_history.asp?docid=16089&ms_num=%27NEFRO-D-23-00014%27
# the url is the same for all the documents. The only thing that changes is the data-identity and numero_manuscrito



# %%
#scrap the data from the url  https://www.editorialmanager.com/nefro/doc_history.asp?docid=16089&ms_num=%27NEFRO-D-23-00014%27

url = 'https://www.editorialmanager.com/nefro/doc_history.asp?docid=16089&ms_num=%27NEFRO-D-23-00014%27'



#open the url
session = requests.Session()
response = session.get(url, headers=headers)
print(response.status_code)

#extract the body
body = response.text


# %%
#There are two tables in the class= 'datatable' in the body
#scrap the second table

data = []

numero_manuscrito = 'NEFRO-D-23-00014'
data_identity = '16089'

soup = BeautifulSoup(body, 'html.parser')
table = soup.find_all('table', class_='datatable')[1]
#print(table)

rows = table.find_all("tr")

for row in rows:
    cells = row.find_all("td")
    if len(cells)>0:
        fecha = cells[0].text.strip()
        carta = cells[1].text.strip()
        destinatario = cells[2].text.strip()
        estado = cells[3].text.strip()
        revision = cells[4].text.strip()
        operador = cells[5].text.strip()
        data.append({"numero_manuscrito": numero_manuscrito, "data_identity": data_identity, "Fecha": fecha, "Carta": carta, "Destinatario": destinatario, "Estado": estado, "Revision": revision, "Operador": operador})

df = pd.DataFrame.from_dict(data)
df


# %%



