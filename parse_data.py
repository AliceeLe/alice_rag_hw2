import requests
from bs4 import BeautifulSoup


pittsburgh_list_html = [
    "https://en.wikipedia.org/wiki/Pittsburgh", 
    "https://www.pittsburghpa.gov/Home",
    "https://www.britannica.com/place/Pittsburgh",
    "https://www.visitpittsburgh.com",
    "https://pittsburghpa.gov/finance/tax-forms",
    "https://www.cmu.edu/about/"
]

pittsburgh_list_pdf = [
    "https://www.pittsburghpa.gov/files/assets/city/v/4/omb/documents/operating-budgets/2025-operating-budget.pdf"
]

def read_pdf(file, input_path, output_path):
    pass 

def read_html(url, input_path, output_path):
    page = requests.get(url)
    soup = BeautifulSoup(page.content, 'html.parser')

    # Example: find the first H2 tag
    h2_tag = soup.find('h2')

def write_txt():
    pass 

