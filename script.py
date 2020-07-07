import pandas as pd
import functools
import requests
import credits
import numpy as np


def get_json_from_jira(url):
    username = credits.username
    password = credits.password
    r = requests.get(url, auth=(username, password))
    data = r.json()
    return data


def get_field(obj, field_name):
    return obj[field_name]


def post_json_to_jira(url, body):
    username = credits.username
    password = credits.password
    r = requests.post(url, json=body, auth=(username, password))
    data = r.json()
    return data


def get_data_frame_from_json(data, keys, columns):
    string_list = []
    for s in data:
        a = ()
        for key in keys:
            a += ((functools.reduce(get_field, key, s)),)
        string_list.append(a)
    data_frame = pd.DataFrame(string_list)
    data_frame = data_frame.rename(columns=columns)
    return data_frame


# Получаем DataFrame проектов
projectsURL = 'https://jira.csssr.io/rest/api/2/project'
projectsData = get_json_from_jira(projectsURL)

projectsKeys = ['key'], ['name']
projectsColumns = {
    0: 'Project Id',
    1: 'Project Name'}

projectsDataFrame = get_data_frame_from_json(projectsData, projectsKeys, projectsColumns)

# Вводим название или ID проекта и проверяем есть ли у нас такой
project = 'Smartbe'
# project = input('Project: ')

while not projectsDataFrame.isin([project]).any().any():
    print('Error! Try again.')
    project = input('Project: ')

# Вводим период времени и конверитим в unix timestamp
dateFrom = '27, 06, 2020'.split(', ')
# dateTo = '03, 06, 2020'.split(', ')

# dateFrom = input('From Date, Month, Year: ').split(', ')
# dateTo = input('To Date, Month, Year: ').split(', ')

# Получаем DataFrame не дев сотрудников
notDevURL = 'https://jira.csssr.io/rest/api/2/group/member?groupname=csssr-notdev'
notDevData = get_json_from_jira(notDevURL)['values']

notDevKeys = ['displayName'], ['key']
notDevColumns = {
    0: 'Name',
    1: 'Key'}

notDevDataFrame = get_data_frame_from_json(notDevData, notDevKeys, notDevColumns)

# Получаем задачи за указанный период времени
'https://jira.csssr.io/rest/api/2/search?maxResults=500&jql=project%20%3D%20GAZ-MPSS%20and%20updated%20%3E%3D%20%222020%2F07%2F01%2000%3A00%22'
issuesInPeriodURL = 'https://jira.csssr.io/rest/api/2/search?maxResults=500&jql=project%20%3D%20' \
                    + project + '%20and%20updated%20%3E%3D%20%22' \
                    + dateFrom[2] + '%2F' \
                    + dateFrom[1] + '%2F' \
                    + dateFrom[0] + '%2000%3A00%22'

issuesInPeriodData = get_json_from_jira(issuesInPeriodURL)

issuesInPeriodKeys = ['id'], ['key'], ['fields', 'issuetype', 'name'], ['fields', 'components'], \
                     ['fields', 'project', 'name'], ['fields', 'summary'], ['fields', 'timeoriginalestimate']
issuesInPeriodColumns = {
    0: 'Issue Id',
    1: 'Issue Key',
    2: 'Issue Type',
    3: 'Components',
    4: 'Project',
    5: 'Summary',
    6: 'Original Estimate'
}

issuesInPeriodDataFrame = get_data_frame_from_json(issuesInPeriodData['issues'], issuesInPeriodKeys,
                                                   issuesInPeriodColumns)

for index, a in issuesInPeriodDataFrame.iterrows():
    if a['Components'] != [] and a['Components'][0]['name'] == 'do_not_analyze':
        issuesInPeriodDataFrame.at[index, 'Components'] = 'do_not_analyze'

issuesInPeriodDataFrame = issuesInPeriodDataFrame.loc[issuesInPeriodDataFrame['Components'] != 'do_not_analyze']

# Вытаскиваем все ворклоги из каждой задачи
print('Начинаю вытаскивать ворклоги из всех задач...')
totalWorklogsData = []
n = 0
n_index = len(issuesInPeriodDataFrame.index)
for issue in issuesInPeriodDataFrame['Issue Id']:
    n += 1
    print(n, " from ", n_index )
    getWorklogFromIssueURL = 'https://jira.csssr.io/rest/api/2/issue/' + issue + '/worklog'
    partWorklogs = get_json_from_jira(getWorklogFromIssueURL)
    totalWorklogsData += partWorklogs['worklogs']

totalWorklogsKeys = ['issueId'], ['author', 'displayName'], ['timeSpentSeconds']
totalWorklogsColumns = {
    0: 'Issue Id',
    1: 'Author',
    2: 'Time Spent'
}

totalWorklogsDataFrame = get_data_frame_from_json(totalWorklogsData, totalWorklogsKeys, totalWorklogsColumns)
totalWorklogsDataFrame = totalWorklogsDataFrame.loc[totalWorklogsDataFrame['Author'].isin(notDevDataFrame['Name']) == False]

# Теперь мерджим дата фреймы финально
finalDataFrame = totalWorklogsDataFrame.merge(issuesInPeriodDataFrame, on='Issue Id', how='outer')
finalDataFrame = finalDataFrame.fillna(0)
finalDataFrame = finalDataFrame.loc[finalDataFrame['Time Spent'] != 0.0]

userDataFrame = finalDataFrame.drop(columns=['Issue Key', 'Time Spent', 'Issue Type', 'Components', 'Project', 'Summary', 'Original Estimate'])
userDataFrame = userDataFrame.groupby('Issue Id')['Author'].apply(lambda x: list(np.unique(x))).reset_index()
userDataFrame['Author'] = userDataFrame['Author'].apply(lambda x: ','.join(map(str, x)))

finalDataFrame = finalDataFrame.merge(userDataFrame, on='Issue Id', how='outer')
finalDataFrame = finalDataFrame.drop(columns=['Author_x']).rename(columns={'Author_y': 'Author'})

finalDataFrame['Issue Key'] = 'https://jira.csssr.io/browse/' + finalDataFrame['Issue Key']
finalDataFrame['Original Estimate'] = (finalDataFrame['Original Estimate'] / 60) / 60
finalDataFrame['Time Spent'] = (finalDataFrame['Time Spent'] / 60) / 60

finalDataFramePivot = finalDataFrame.pivot_table(index=['Issue Key', 'Summary', 'Issue Type', 'Author', 'Original Estimate'],
                                                 values=['Time Spent'], aggfunc=np.sum)
finalDataFrame = finalDataFramePivot.reindex(finalDataFramePivot.sort_values(by='Issue Type', ascending=False).index)

finalDataFrame.to_csv('result.csv')
