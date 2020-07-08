#!/usr/local/bin/python3

import pandas as pd
import functools
import requests
import credits
import numpy as np
from datetime import datetime


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

# project = 'GMPSS'
projects = input('Project(s): ').split(', ')

checkedProject = ''
wrongProject = ''
for s in projects:
    if projectsDataFrame.isin([s]).any().any():
        checkedProject = 'ok'
    else:
        checkedProject = 'not ok'
        wrongProject = s
while checkedProject != 'ok':
    print('Wrong! Project ' + wrongProject + ' is not in the Jira. Try again.')
    projects = input('Project(s): ').split(', ')
    for s in projects:
        if projectsDataFrame.isin([s]).any().any():
            checkedProject = 'ok'
        else:
            checkedProject = 'not ok'
            wrongProject = s

# Вводим период времени и конверитим в unix timestamp

# dateFrom = '05, 07, 2020'.split(', ')
dateFrom = input('From Date, Month, Year: ').split(', ')

# Получаем DataFrame не дев сотрудников
notDevDataFrame = pd.read_csv('notDev.csv')

# Получаем задачи за указанный период времени
projectForJQL = '%2C%20'.join(projects)
issuesInPeriodURL = 'https://jira.csssr.io/rest/api/2/search?maxResults=500&jql=project%20in%20' \
                    '(' + projectForJQL + ')%20and%20updated%20%3E%3D%20%22' \
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

issuesDataFrame = issuesInPeriodDataFrame.loc[issuesInPeriodDataFrame['Components'] != 'do_not_analyze']

# Вытаскиваем все ворклоги из каждой задачи
print('Начинаю вытаскивать ворклоги из всех задач...')
totalWorklogsData = []

n = 0
n_index = len(issuesDataFrame.index)
for issue in issuesDataFrame['Issue Id']:
    n += 1
    print(n, " from ", n_index)
    getWorklogFromIssueURL = 'https://jira.csssr.io/rest/api/2/issue/' + issue + '/worklog'
    partWorklogs = get_json_from_jira(getWorklogFromIssueURL)
    totalWorklogsData += partWorklogs['worklogs']

totalWorklogsKeys = ['issueId'], ['author', 'displayName'], ['timeSpentSeconds'], ['created']
totalWorklogsColumns = {
    0: 'Issue Id',
    1: 'Author',
    2: 'Time Spent',
    3: 'Worklog created'
}

totalWorklogsDataFrame = get_data_frame_from_json(totalWorklogsData, totalWorklogsKeys, totalWorklogsColumns)
totalWorklogsDataFrame = totalWorklogsDataFrame.loc[
    totalWorklogsDataFrame['Author'].isin(notDevDataFrame['Name']) == False]

# Делаем датафрейм с ворклогами в периоде указанной даты
timestampFrom = str(int(datetime(int(dateFrom[2]), int(dateFrom[1]), int(dateFrom[0])).timestamp()))

for index, a in totalWorklogsDataFrame.iterrows():
    totalWorklogsDataFrame.at[index, 'Worklog created'] = str(int(datetime(int(a['Worklog created'][:4]),
                                                                           int(a['Worklog created'][5:7]),
                                                                           int(a['Worklog created'][8:10]))
                                                                  .timestamp()))

periodWorklogsDataFrame = totalWorklogsDataFrame.loc[totalWorklogsDataFrame['Worklog created'] > timestampFrom]
periodWorklogsDataFrame = periodWorklogsDataFrame.drop(
    columns=['Author', 'Worklog created']).rename(
    columns={'Time Spent': 'Time Spent Period'})

periodWorklogsDataFrame['Time Spent Period'] = (periodWorklogsDataFrame['Time Spent Period'] / 60) / 60

periodWorklogsDataFramePivot = periodWorklogsDataFrame.pivot_table(index=['Issue Id'], values=['Time Spent Period'],
                                                                   aggfunc=np.sum)

# Теперь мерджим дата фреймы финально
finalDataFrame = totalWorklogsDataFrame.merge(issuesInPeriodDataFrame, on='Issue Id', how='outer')
finalDataFrame = finalDataFrame.fillna(0)
finalDataFrame = finalDataFrame.loc[finalDataFrame['Time Spent'] != 0.0]

userDataFrame = finalDataFrame.drop(columns=['Issue Key', 'Time Spent', 'Issue Type', 'Components', 'Project',
                                             'Summary', 'Original Estimate'])
userDataFrame = userDataFrame.groupby('Issue Id')['Author'].apply(lambda x: list(np.unique(x))).reset_index()
userDataFrame['Author'] = userDataFrame['Author'].apply(lambda x: ', '.join(map(str, x)))

finalDataFrame = finalDataFrame.merge(userDataFrame, on='Issue Id', how='outer')
finalDataFrame = finalDataFrame.drop(columns=['Author_x']).rename(columns={'Author_y': 'Worklog Authors'})

finalDataFrame['Issue Key'] = 'https://jira.csssr.io/browse/' + finalDataFrame['Issue Key']
finalDataFrame['Original Estimate'] = (finalDataFrame['Original Estimate'] / 60) / 60
finalDataFrame['Time Spent'] = (finalDataFrame['Time Spent'] / 60) / 60

finalDataFramePivot = finalDataFrame.pivot_table(index=['Issue Id', 'Issue Key', 'Summary', 'Issue Type',
                                                        'Worklog Authors', 'Original Estimate'],
                                                 values=['Time Spent'],
                                                 aggfunc=np.sum)

finalDataFrame = finalDataFramePivot.reindex(finalDataFramePivot.sort_values(by='Issue Type', ascending=False).index)
finalDataFrame = finalDataFrame.join(periodWorklogsDataFramePivot, on='Issue Id', how='outer').reset_index()
finalDataFrame = finalDataFrame.drop(columns=['Issue Id'])
finalDataFrame = finalDataFrame.loc[finalDataFrame['Time Spent Period'].isnull() == False]
finalDataFrame = finalDataFrame.round(2).reset_index().drop(columns=['index'])

finalDataFrame.to_csv('result.csv')
