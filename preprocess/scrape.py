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

def get_html(url):
    headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/107.0.0.0 Safari/537.36'} # Add user-agent to avoid being blocked
    response = requests.get(url, headers=headers)

    if response.status_code == 200:
        html_content = response.text
        return html_content
    else:
        print(f"Failed to retrieve the webpage. Status code: {response.status_code}")
        exit()

def read_html(url, output_path):
    try:
        # Extract content 
        html_content = get_html(url)
        soup = BeautifulSoup(html_content, "html.parser")
        text = soup.get_text(separator="\n", strip=True)

        # Write to .txt
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(text)
        print("Extraction complete.")
    except Exception as e:
        print("An error occurred:", e) 

if __name__=="__main__":
    # Get starting url 
    # Get a list of relevant urls from web crawler
    # Iterate through the list and call read_html
    # Standardize data???
    read_html("https://www.cmu.edu/")