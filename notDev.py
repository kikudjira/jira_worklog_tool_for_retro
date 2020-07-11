import pandas as pd
import functools
import requests
import credits


def get_json_from_jira(url):
    r = requests.get(url, auth=(credits.username, credits.password))
    data = r.json()
    return data


def get_field(obj, field_name):
    return obj[field_name]


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


# Получаем DataFrame не дев сотрудников (может только админ джиры)
notDevURL = credits.baseJiraURL + '/rest/api/2/group/member?groupname=notdev'
notDevData = get_json_from_jira(notDevURL)['values']

notDevKeys = ['displayName'], ['key']
notDevColumns = {
    0: 'Name',
    1: 'Key'}

notDevDataFrame = get_data_frame_from_json(notDevData, notDevKeys, notDevColumns).to_csv('notDev.csv')
