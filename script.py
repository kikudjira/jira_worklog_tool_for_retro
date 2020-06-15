import pandas as pd
import requests
import credits

url = 'https://jira.csssr.io/rest/api/2/issue/GTP-7'
headers = { "Accept": "application/json", "Content-Type": "application/json" }
username = credits.username
password = credits.password
r = requests.get(url, headers=headers, auth=(username,password))

df = pd.read_json(r.text)
df.to_csv('source.csv')
