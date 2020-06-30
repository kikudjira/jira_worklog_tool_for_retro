import pandas as pd
import json
import requests
import credits


def json_from_jira(url):
    username = credits.username
    password = credits.password
    r = requests.get(url, auth=(username, password))
    data = r.json()
    return data


url_get_projects = 'https://jira.csssr.io/rest/api/2/project'
data_projects = json_from_jira(url_get_projects)

list_projects = []
for string in data_projects:
    a = string['key'], \
        string["name"]
    list_projects.append(a)

data_frame_projects = pd.DataFrame(list_projects).rename(columns=
{
    0: 'Project Id',
    1: 'Project Name',
}).to_csv('projects.csv')

project = input('Project Id: ')
time_update = input('Days ago: ')

# project = 'GMPSS'
# time_update = '7'

url_get_updated = 'https://jira.csssr.io/rest/api/2/search?jql=project%20%3D%20' + project + '%20and%20updatedDate%20%3E%3D%20-' + time_update + 'd&maxResults=500'

data_updated = json_from_jira(url_get_updated)

if data_updated['total'] > 500:
    print('Не все задачи попали в таблицу, укажите период меньше текущего')

list_updated = []
for string in data_updated['issues']:
    a = string['key'], \
        'https://jira.csssr.io/browse/' + string['key'], \
        string["fields"]['timeoriginalestimate'], \
        string['fields']['issuetype']['name'], \
        string['fields']['summary']
    list_updated.append(a)

data_frame_updated = pd.DataFrame(list_updated).rename(columns=
{
    0: 'Issue Id',
    1: 'URL',
    2: 'Original Estimate',
    3: 'Issue Type',
    4: 'Summary'
})

data_frame_updated.to_csv('updated.csv')
