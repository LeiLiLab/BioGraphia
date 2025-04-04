import requests
from bs4 import BeautifulSoup
from dataclasses import dataclass
import unittest
from unittest.mock import patch, MagicMock

# only works for Pubmed; need to add other scrapers for other databases

@dataclass
class PubMedArticle:
    pmid: str
    title: str
    abstract: str
    url: str

class PubMedScraper:
    def __init__(self):
        self.base_url = "https://pubmed.ncbi.nlm.nih.gov/"
    
    def extract_from_url(self, url: str) -> PubMedArticle:
        """Extract article information from PubMed URL."""
        try:
            response = requests.get(url, proxies={"http": None, "https": None})
            # Very strange issue - using None for proxies prevents network errors
            # response = requests.get(url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract PMID from URL
            pmid = url.rstrip('/').split('/')[-1]
        
            # Extract title
            title = soup.find('h1', {'class': 'heading-title'}).text.strip()
            
            # Extract abstract
            abstract_div = soup.find('div', {'class': 'abstract-content selected'})
            abstract = ""
            if abstract_div:
                paragraphs = abstract_div.find_all('p')
                abstract_parts = []
                for p in paragraphs:
                    subtitle = p.find('strong', {'class': 'sub-title'})
                    if subtitle:
                        abstract_parts.append(f"{subtitle.text.strip()} {p.text.replace(subtitle.text, '').strip()}")
                    else:
                        abstract_parts.append(p.text.strip())
                abstract = " ".join(abstract_parts)
            
            return PubMedArticle(
                pmid=pmid,
                title=title,
                abstract=abstract,
                url=url
            )
            
        except Exception as e:
            raise Exception(f"Failed to extract PubMed article: {str(e)}") 
        
class TestPubMedScraper(unittest.TestCase):
    def test_extract_from_url(self):
        url = "https://pubmed.ncbi.nlm.nih.gov/29795461/"
        scraper = PubMedScraper()
        article = scraper.extract_from_url(url)

        # Print extracted details for debugging
        print("Extracted PMID:", article.pmid)
        print("Extracted Title:", article.title)
        print("Extracted Abstract:", article.abstract)
        print("Extracted URL:", article.url)

        # Assertions
        self.assertEqual(article.pmid, "29795461")
        self.assertTrue(len(article.title) > 0)
        self.assertTrue(len(article.abstract) > 0)

import json

def extract_article_to_json(url):
    """
    Extract PubMed article information and return as JSON format.

    Parameters:
        url (str): URL of the PubMed article.

    Returns:
        str: JSON formatted string containing title and abstract.
    """
    scraper = PubMedScraper()
    try:
        article = scraper.extract_from_url(url)
        # Return JSON formatted data
        return json.dumps({
            "title": article.title,
            "abstract": article.abstract
        }, ensure_ascii=False, indent=4)
    except Exception as e:
        raise Exception(f"Failed to extract article: {str(e)}")

if __name__ == '__main__':
    # unittest.main()        

    url = "https://pubmed.ncbi.nlm.nih.gov/29795461/"  # Replace with the URL to extract

    result = extract_article_to_json(url)

    print(result)