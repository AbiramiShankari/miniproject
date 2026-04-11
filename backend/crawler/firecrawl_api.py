import os
from firecrawl import FirecrawlApp
from dotenv import load_dotenv

load_dotenv()

# We initialize the FirecrawlApp without an API key which may throw an error 
# if not provided in env, but we catch it in our fallback.
class CrawlerService:
    def __init__(self):
        self.api_key = os.getenv("FIRECRAWL_API_KEY")
        if self.api_key:
            self.app = FirecrawlApp(api_key=self.api_key)
        else:
            self.app = None

    def crawl_company_questions(self, company_name: str):
        """
        Crawls the web for interview questions of a specific company using Firecrawl.
        """
        if not self.app:
            return {
                "error": "No FIRECRAWL_API_KEY found",
                "company": company_name,
                "questions": [
                    f"Tell me about a time you faced a challenge at {company_name}?",
                    f"Why do you want to join {company_name}?",
                    "Can you explain your final year project?",
                    "What are your biggest strengths and weaknesses?",
                    f"How does {company_name} align with your career goals?"
                ]
            }

        try:
            # Using Firecrawl extract on a common interview platform (can be customized)
            result = self.app.scrape_url(
                url=f"https://www.geeksforgeeks.org/tag/{company_name.lower()}-interview-questions/",
                params={
                    'formats': ['extract'],
                    'extract': {
                        'prompt': f'Extract a list of top 5 interview questions for {company_name}.'
                    }
                }
            )
            return result
        except Exception as e:
            return {
                "error": str(e),
                "company": company_name,
                "questions": [
                    f"Fallback Question 1 for {company_name}?",
                    f"Fallback Question 2 for {company_name}?",
                    "Fallback Question 3?"
                ]
            }

crawler = CrawlerService()
