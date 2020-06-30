import pandas as pd
import json
import requests
import credits

project = 'GMPSS'
time_update = '-7d'

url = 'https://jira.csssr.io/rest/api/2/search?jql=project%20%3D%20' + project + '%20and%20updatedDate%20%3E%3D%20' + time_update + '&maxResults=500'

username = credits.username
password = credits.password

r = requests.get(url, auth=(username, password))
data = r.json()

# with open('data.json', 'w') as f:
#     json.dump(data, f)

if data['total'] > 500:
    print('Не все задачи попали в таблицу, укажите период меньше текущего')

parsing_dict = []
for string in data['issues']:
    a = \
        string['key'],  'https://jira.csssr.io/browse/' + string['key'], \
        string["fields"]['timeoriginalestimate'], \
        string['fields']['issuetype']['name'], \
        string['fields']['summary']
    parsing_dict.append(a)

data_frame = pd.DataFrame(parsing_dict).rename(columns=
{
    0: 'Issue Id',
    1: 'URL',
    2: 'Original Estimate',
    3: 'Issue Type',
    4: 'Summary'
})

data_frame.to_csv('test.csv')
