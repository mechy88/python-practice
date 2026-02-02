from bs4 import BeautifulSoup
import requests
import certifi

# # works with certifi to avoid SSL certificate errors
# html_text = requests.get('http://httpforever.com/')

html_text = requests.get('https://timesjobs.com/job-search?keywords=%22application+developer%22&refreshed=true', verify=False)

# Create new instance of BeautifulSoup with the content and parser
soup = BeautifulSoup(html_text.text, 'lxml')
# jobs = soup.find_all("div", class_ = "p-4 md:p-6 bg-white rounded-xl mb-4 shadow-sm relative srp-card")
jobs = soup.find_all("div")
print(soup)