#!/usr/local/bin/python3
# coding=utf-8
import pandas as pd
import functools
import requests
import credits
import numpy as np
import os
from datetime import datetime


def get_json_from_jira(url):
    r = requests.get(url, auth=(credits.username, credits.password))
    data = r.json()
    return data


def get_field(obj, field_name):
    return obj[field_name]


def post_json_to_jira(url, body):
    r = requests.post(url, json=body, auth=(credits.username, credits.password))
    data = r.json()
    return data


def get_data_frame_from_json(data, keys, columns):
    string_list = []
    for STR in data:
        lst = ()
        for key in keys:
            lst += ((functools.reduce(get_field, key, STR)),)
        string_list.append(lst)
    data_frame = pd.DataFrame(string_list)
    data_frame = data_frame.rename(columns=columns)
    return data_frame


# Получаем путь до директории и файла скрипта в системе
dirName, fileName = os.path.split(os.path.abspath(__file__))

# Получаем DataFrame проектов
projectsURL = credits.baseJiraURL + '/rest/api/2/project'
projectsData = get_json_from_jira(projectsURL)

projectsKeys = ['key'], ['name']
projectsColumns = {
    0: 'Project Id',
    1: 'Project Name'
}

projectsDataFrame = get_data_frame_from_json(
    projectsData,
    projectsKeys,
    projectsColumns
)

# Вводим название или ID проекта и проверяем есть ли у нас такой
projects = input('Project(s): ').split(', ')

checkedProject = ''
wrongProject = ''
for STR in projects:
    if projectsDataFrame.isin([STR]).any().any():
        checkedProject = 'ok'
    else:
        checkedProject = 'not ok'
        wrongProject = STR
while checkedProject != 'ok':
    print('Wrong! Project ' + wrongProject + ' is not in the Jira. Try again.')
    projects = input('Project(s): ').split(', ')
    for STR in projects:
        if projectsDataFrame.isin([STR]).any().any():
            checkedProject = 'ok'
        else:
            checkedProject = 'not ok'
            wrongProject = STR

# Вводим период времени и конверитим в unix timestamp
dateFrom = input('From Date(##), Month(##), Year(####): ').split(', ')

# ToDo: Написать валидатор строчки с датой

# checkedDateFrom = ''
# wrongDateFrom = ''
# for STR in dateFrom:
#     if STR:
#         checkedDateFrom = 'ok'
#     else:
#         checkedDateFrom = 'not ok'
#         wrongDateFrom = STR
# while checkedDateFrom != 'ok':
#     print('Wrong! Project ' + wrongDateFrom + ' is not in the Jira. Try again.')
#     projects = input('Project(s): ').split(', ')
#     for STR in projects:
#         if projectsDataFrame.isin([STR]).any().any():
#             checkedDateFrom = 'ok'
#         else:
#             checkedDateFrom = 'not ok'
#             wrongDateFrom = STR

timestampFrom = str(int(datetime(int(dateFrom[2]), int(dateFrom[1]), int(dateFrom[0])).timestamp()))

# Получаем DataFrame не дев сотрудников
notDevDataFrame = pd.read_csv(str(dirName) + '/notDev.csv')

# Получаем задачи с апдейтом за указанный период времени
projectForJQL = '%2C%20'.join(projects)
issuesInPeriodURL = credits.baseJiraURL + '/rest/api/2/search?maxResults=500&jql=project%20in%20' \
                                          '(' + projectForJQL + ')%20and%20updated%20%3E%3D%20%22' \
                    + dateFrom[2] + '%2F' \
                    + dateFrom[1] + '%2F' \
                    + dateFrom[0] + '%2000%3A00%22'

issuesInPeriodData = get_json_from_jira(issuesInPeriodURL)

issuesInPeriodKeys = ['id'], ['key'], ['fields', 'issuetype', 'name'], ['fields', 'components'], \
                     ['fields', 'project', 'name'], ['fields', 'summary'], ['fields', 'timeoriginalestimate'], \
                     ['fields', 'status', 'name']

issuesInPeriodColumns = {
    0: 'Issue Id',
    1: 'Issue Key',
    2: 'Issue Type',
    3: 'Components',
    4: 'Project',
    5: 'Summary',
    6: 'Original Estimate',
    7: 'Status'
}

issuesInPeriodDataFrame = get_data_frame_from_json(
    issuesInPeriodData['issues'],
    issuesInPeriodKeys,
    issuesInPeriodColumns
)

# Делаем проверки на компонент do_not_analyze и отбрасываем эти значения
for index, a in issuesInPeriodDataFrame.iterrows():
    if a['Components'] != [] and a['Components'][0]['name'] == 'do_not_analyze':
        issuesInPeriodDataFrame.at[index, 'Components'] = 'do_not_analyze'

issuesDataFrame = issuesInPeriodDataFrame.loc[issuesInPeriodDataFrame['Components'] != 'do_not_analyze']

# Вытаскиваем все ворклоги из каждой задачи
print('Начинаю вытаскивать ворклоги из всех задач...')

totalWorklogsData = []
n = 0

for issue in issuesDataFrame['Issue Id']:
    n += 1
    print(n, " from ", len(issuesDataFrame.index))
    getWorklogFromIssueURL = credits.baseJiraURL + '/rest/api/2/issue/' + issue + '/worklog'
    partWorklogs = get_json_from_jira(getWorklogFromIssueURL)
    totalWorklogsData += partWorklogs['worklogs']

totalWorklogsKeys = ['issueId'], ['author', 'displayName'], ['timeSpentSeconds'], ['created']
totalWorklogsColumns = {
    0: 'Issue Id',
    1: 'Author',
    2: 'Time Spent',
    3: 'Worklog created'
}

totalWorklogsDataFrame = get_data_frame_from_json(
    totalWorklogsData,
    totalWorklogsKeys,
    totalWorklogsColumns
)

# Делаем проверку на наличие ворклогов сотрудников не девелоперов
totalWorklogsDataFrame = totalWorklogsDataFrame.loc[totalWorklogsDataFrame['Author'].isin
                                                    (notDevDataFrame['Name']) == False]

# Делаем датафрейм с ворклогами в периоде указанной даты
for index, a in totalWorklogsDataFrame.iterrows():
    totalWorklogsDataFrame.at[index, 'Worklog created'] = str(int(datetime(int(a['Worklog created'][:4]),
                                                                           int(a['Worklog created'][5:7]),
                                                                           int(a['Worklog created'][8:10]))
                                                                  .timestamp())
                                                              )

periodWorklogsDataFrame = totalWorklogsDataFrame.loc[totalWorklogsDataFrame['Worklog created'] > timestampFrom].drop(
    columns=['Author', 'Worklog created']
).rename(
    columns={'Time Spent': 'Time Spent Period'}
)

periodWorklogsDataFrame['Time Spent Period'] = (periodWorklogsDataFrame['Time Spent Period'] / 60) / 60

periodWorklogsDataFramePivot = periodWorklogsDataFrame.pivot_table(
    index=['Issue Id'],
    values=['Time Spent Period'],
    aggfunc=np.sum
)

# Теперь мерджим дата фреймы финально
resultDataFrame = totalWorklogsDataFrame.merge(issuesInPeriodDataFrame, on='Issue Id', how='outer').fillna(0)
resultDataFrame = resultDataFrame.loc[resultDataFrame['Time Spent'] != 0.0]

# Собираем авторов ворклогов
userDataFrame = resultDataFrame.drop(
    columns=['Issue Key', 'Time Spent', 'Issue Type', 'Components', 'Project', 'Summary', 'Original Estimate']
).groupby(
    'Issue Id')['Author'
].apply(
    lambda x: list(np.unique(x))
).reset_index()

userDataFrame['Author'] = userDataFrame['Author'].apply(lambda x: ', '.join(map(str, x)))

# Добавляем колонку с авторами варклога
resultDataFrame = resultDataFrame.drop(
    columns=['Author']
).merge(
    userDataFrame, on='Issue Id', how='outer'
).rename(
    columns={'Author': 'Worklog Authors'}
)

# Добавляем колонку с урлом на задачу
resultDataFrame['Issue Key URL'] = credits.baseJiraURL + '/browse/' + resultDataFrame['Issue Key']

# Переводим время в часы
resultDataFrame['Original Estimate'] = (resultDataFrame['Original Estimate'] / 60) / 60
resultDataFrame['Time Spent'] = (resultDataFrame['Time Spent'] / 60) / 60

# Делаем сводный датафрейм
resultDataFramePivot = resultDataFrame.pivot_table(
    index=['Issue Id', 'Issue Key URL', 'Issue Key', 'Summary', 'Issue Type', 'Status', 'Worklog Authors',
           'Original Estimate'],
    values=['Time Spent'],
    aggfunc=np.sum
)

# Делаем сортировку по типу задач и добавляем сумму ворклогов за период
resultDataFrame = resultDataFramePivot.reindex(
    resultDataFramePivot.sort_values(by='Issue Type', ascending=False).index
).join(
    periodWorklogsDataFramePivot, on='Issue Id', how='outer'
).reset_index().drop(
    columns='Issue Id')

# Готовим датафрейм для сохранения и сохраняем в csv
resultDataFrame = resultDataFrame.loc[resultDataFrame['Time Spent Period'].isnull() == False]
resultDataFrame = resultDataFrame.round(2).reset_index().drop(columns=['index'])
resultDataFrame.to_csv('result.csv', encoding='utf-8', index=False, sep='\t', decimal=',')
