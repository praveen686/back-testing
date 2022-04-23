import requests
response = requests.get("https://www.google.com")
data = response.text
print(data)
