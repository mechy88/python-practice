from bs4 import BeautifulSoup
import requests
import certifi

# # works with certifi to avoid SSL certificate errors
# html_text = requests.get('http://httpforever.com/')

html_text = requests.get('https://timesjobs.com/job-search?keywords=%22application+developer%22&refreshed=true', verify=False)
print(html_text.text)