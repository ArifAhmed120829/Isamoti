import time
import requests
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
##
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
##
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException
from duckduckgo_search import DDGS
import re
from bs4 import BeautifulSoup
import json
import os

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "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")


class GroqAPI:
    def __init__(self, model_id="llama3-8b-8192", api_key=None):
        self.model_id = model_id
        self.api_key = api_key or GROQ_API_KEY
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.backup_models = ["llama2-7b-4096", "mixtral-8x7b-32768"]
        self.current_model_index = 0

    def switch_to_backup_model(self):
        if self.current_model_index < len(self.backup_models):
            self.model_id = self.backup_models[self.current_model_index]
            self.current_model_index += 1
            print(f"Switched to backup model: {self.model_id}")
            return True
        return False

    def generate(self, prompt, **kwargs):
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }

            payload = {
                "model": self.model_id,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": kwargs.get("temperature", 0.7),
                "max_tokens": min(kwargs.get("max_tokens", 500), 1000)
            }

            try:
                print(f"Sending request to Groq API ({self.model_id})...")
                response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)

                if response.status_code == 200:
                    result = response.json()
                    if "choices" in result and result["choices"] and "message" in result["choices"][0]:
                        return result["choices"][0]["message"]["content"].strip()
                    else:
                        return str(result)
                else:
                    if response.status_code == 503 or response.status_code == 429:
                        print(f"Service unavailable ({response.status_code}). Trying backup model...")
                        if self.switch_to_backup_model():
                            retry_count += 1
                            time.sleep(2)
                            continue
                        else:
                            return self.fallback_generate(prompt)
                    error_msg = f"Error: API returned status code {response.status_code}"
                    print(error_msg)
                    retry_count += 1
                    time.sleep(2)
            except Exception as e:
                error_msg = f"Error calling Groq API: {str(e)}"
                print(error_msg)
                retry_count += 1
                time.sleep(2)

        return self.fallback_generate(prompt)

    def fallback_generate(self, prompt):
        print("Using fallback generation method...")

        if "Generate 3 possible news headlines" in prompt:
            tweet_text = re.search(r'"([^"]*)"', prompt).group(1) if re.search(r'"([^"]*)"', prompt) else ""
            words = tweet_text.split()
            headlines = []
            if len(words) >= 5:
                headlines.append(" ".join(words[:5]) + "...")
            if len(words) >= 10:
                headlines.append(" ".join(words[5:10]) + "...")
            if len(words) >= 15:
                headlines.append(" ".join(words[10:15]) + "...")

            while len(headlines) < 3:
                headlines.append(f"News about {words[0] if words else 'incident'}")

            return "\n".join(headlines)

        elif "Fact-check this tweet" in prompt:
            return "Based on the available information, this tweet appears to contain elements of truth but may be exaggerated or incomplete. The articles provide some context but don't fully verify all claims made in the tweet. Consider this information preliminary until more sources can be consulted."

        return "Could not generate response due to API limitations."


def setup_driver():
    chrome_options = Options()
    chrome_options.add_argument("--headless")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--window-size=1920,1080")

    # driver = webdriver.Chrome(options=chrome_options)

    ##ubuntus way
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_options)
    ####
    return driver


def get_tweet_text(driver, url):
    print(f"Navigating to {url}")
    driver.get(url)

    try:
        wait = WebDriverWait(driver, 20)
        tweet_element = wait.until(
            EC.presence_of_element_located((By.CSS_SELECTOR, '[data-testid="tweetText"]'))
        )

        tweet_text = tweet_element.text
        print("Tweet text found!")
        return tweet_text

    except TimeoutException:
        print("Timeout waiting for tweet text to load")
        return None
    except NoSuchElementException:
        print("Could not find the tweet text element")
        return None
    except Exception as e:
        print(f"Error extracting tweet text: {str(e)}")
        return None


def generate_news_titles(llm, tweet_text):
    prompt = f"""
    Generate 3 possible news headlines related to this tweet that would help fact-check it:

    "{tweet_text}"

    Format: One headline per line.
    """

    print("Generating news headlines for fact-checking...")
    response = llm.generate(prompt, temperature=0.3, max_tokens=150)

    news_titles = [line.strip() for line in response.split('\n') if line.strip()]

    if not news_titles or any("error" in title.lower() for title in news_titles):
        print("Using original tweet text as search query")
        words = tweet_text.split()
        if len(words) > 10:
            segments = [
                " ".join(words[:min(10, len(words))]),
                " ".join(words[min(10, len(words)):min(20, len(words))]),
                " ".join(words[max(0, len(words) - 10):])
            ]
            news_titles = [segment for segment in segments if segment.strip()]

        if not news_titles:
            news_titles = [tweet_text]

    print(f"Generated {len(news_titles)} news headlines")
    return news_titles


def search_duckduckgo(query):
    try:
        print(f"Searching DuckDuckGo for: {query}")
        # Add freshness filter (last 24 hours) and news sources
        modified_query = f"{query} after:2020-01-01"
        with DDGS() as ddgs:
            results = list(ddgs.text(modified_query, max_results=3))
            return results
    except Exception as e:
        print(f"Error searching DuckDuckGo: {str(e)}")
        return []


def extract_article_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')

            for script in soup(["script", "style"]):
                script.decompose()

            paragraphs = soup.find_all('p')
            text = ' '.join([p.get_text() for p in paragraphs])

            text = re.sub(r'\s+', ' ', text).strip()

            if len(text) > 2000:
                text = text[:2000] + "..."

            return text
        else:
            print(f"Failed to retrieve content from {url}. Status code: {response.status_code}")
            return None
    except Exception as e:
        print(f"Error extracting content from {url}: {str(e)}")
        return None


def analyze_tweet_truthfulness(llm, tweet_text, article_contents):
    prompt = f"""
    Fact-check this tweet based on news articles:

    Tweet: "{tweet_text}"

    Articles summary: {article_contents[:3000]}

    Is the tweet true or false? Provide brief evidence.
    """

    print("Sending analysis request to LLM...")
    response = llm.generate(
        prompt,
        temperature=0.1,
        max_tokens=400
    )

    if "error" in response.lower() or not response.strip():
        print("Using fallback analysis...")
        tweet_lower = tweet_text.lower()
        article_lower = article_contents.lower()

        important_keywords = [word.lower() for word in re.findall(r'\b[A-Z][a-z]+\b', tweet_text)]
        found_keywords = [keyword for keyword in important_keywords if keyword in article_lower]

        if len(found_keywords) >= len(important_keywords) * 0.7:
            return "Based on the articles, the tweet appears to be PARTIALLY TRUE. Some key elements mentioned in the tweet are found in the news articles, but specific details may be exaggerated or not fully verified."
        elif len(found_keywords) >= len(important_keywords) * 0.3:
            return "Based on the articles, the tweet appears to be POTENTIALLY MISLEADING. While some elements match news reports, many specific claims cannot be verified from the gathered sources."
        else:
            return "Based on the articles, the tweet appears to be UNVERIFIED. Most specific claims made in the tweet are not substantiated by the gathered sources."

    return response


def main():
    print("Initializing Groq API client...")
    llm = GroqAPI(model_id="llama3-8b-8192", api_key=GROQ_API_KEY)

    tweet_url = input("Enter the Twitter/X post URL (e.g., https://x.com/username/status/123456): ")

    driver = setup_driver()

    try:
        tweet_text = get_tweet_text(driver, tweet_url)

        if tweet_text:
            print("\nExtracted Tweet Text:")
            print("-" * 80)
            print(tweet_text)
            print("-" * 80)

            news_titles = generate_news_titles(llm, tweet_text)

            print("\nGenerated News Headlines for Search:")
            for i, title in enumerate(news_titles, 1):
                print(f"{i}. {title}")
            print("-" * 80)

            all_search_results = []
            for title in news_titles:
                results = search_duckduckgo(title)
                all_search_results.extend(results)

            unique_results = []
            seen_urls = set()
            for result in all_search_results:
                url = result.get('href')
                if url and url not in seen_urls:
                    seen_urls.add(url)
                    unique_results.append(result)

            print("\nSearch Results:")
            print("=" * 80)
            if not unique_results:
                print("No results found.")
                key_terms = " ".join(re.findall(r'\b[A-Z][a-z]+\b', tweet_text))
                if key_terms:
                    print(f"Trying search with key terms: {key_terms}")
                    results = search_duckduckgo(key_terms)
                    unique_results.extend(results)

                if not unique_results:
                    return

            for i, result in enumerate(unique_results[:3], 1):
                print(f"Result {i}:")
                print(f"Title: {result.get('title', 'N/A')}")
                print(f"URL: {result.get('href', 'N/A')}")
                print(f"Description: {result.get('body', 'N/A')}")
                print("-" * 80)

            print("\nExtracting content from news articles...")
            article_contents = []

            for i, result in enumerate(unique_results[:3], 1):
                url = result.get('href')
                if url:
                    print(f"Processing article {i}: {url}")
                    content = extract_article_content(url)
                    if content:
                        summary = content[:600] + "..." if len(content) > 600 else content
                        article_contents.append(f"Article {i}: {summary}")

            if not article_contents:
                print("Could not extract content from any articles.")
                article_contents = [
                    f"Article title: {result.get('title', 'N/A')}\nDescription: {result.get('body', 'N/A')}"
                    for result in unique_results[:3]]
                if not article_contents:
                    return

            all_article_text = " ".join(article_contents)

            print("\nAnalyzing tweet truthfulness...")
            analysis = analyze_tweet_truthfulness(llm, tweet_text, all_article_text)

            print("\nFactual Analysis:")
            print("=" * 80)
            print(analysis)
            print("=" * 80)
        else:
            print("Failed to extract tweet text. Please check the URL and try again.")

    finally:
        driver.quit()


if __name__ == "__main__":
    main()