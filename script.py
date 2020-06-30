import pandas as pd
import json
import requests
import credits

url = 'https://jira.csssr.io/rest/api/2/issue/GTP-7/worklog'
#headers = { "Accept": "application/json", "Content-Type": "application/json" }
username = credits.username
password = credits.password

r = requests.get(url, auth=(username,password))
data = r.json()
with open('data.json', 'w') as f:
    json.dump(data, f)

# df = pd.read_json('data.json')
# df.to_csv('data.csv')
