from typing import List, Dict, Any, Optional
from anthropic import Anthropic
import os
from datetime import datetime, timedelta, timezone
import json
from dotenv import load_dotenv
import logging
from dateutil import parser

logger = logging.getLogger(__name__)

class AnthropicService:
    def __init__(self):
        load_dotenv()
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            logger.error("ANTHROPIC_API_KEY was NOT FOUND in the environment.") # Keep this error for safety
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        
        # Initialize the client as per latest SDK usage
        self.client = Anthropic(api_key=api_key)
        
        self.allowed_domains = [
            "reuters.com", "apnews.com", "bbc.com", "npr.org", "localnews.com",
            "nytimes.com", "washingtonpost.com", "theguardian.com", "thehindu.com",
            "indianexpress.com", "timesofindia.indiatimes.com"
        ]
        self.model = "claude-3-5-sonnet-latest" # Use a model that supports web search from the docs

    def _parse_published_date(self, date_str: Optional[str]) -> Optional[datetime]:
        if not date_str:
            return None
        try:
            # Handle relative dates like "X days ago"
            if "days ago" in date_str.lower():
                days = int(date_str.lower().split(" ")[0])
                return datetime.now(timezone.utc) - timedelta(days=days)
            if "hours ago" in date_str.lower():
                hours = int(date_str.lower().split(" ")[0])
                return datetime.now(timezone.utc) - timedelta(hours=hours)
            if "minutes ago" in date_str.lower():
                minutes = int(date_str.lower().split(" ")[0])
                return datetime.now(timezone.utc) - timedelta(minutes=minutes)
            # Handle "yesterday"
            if "yesterday" in date_str.lower():
                return datetime.now(timezone.utc) - timedelta(days=1)
            
            # Attempt to parse other common date formats
            parsed_date = parser.parse(date_str)
            # If the parsed date is naive, assume UTC as per Anthropic docs and general best practice
            if parsed_date.tzinfo is None or parsed_date.tzinfo.utcoffset(parsed_date) is None:
                parsed_date = parsed_date.replace(tzinfo=timezone.utc)
            return parsed_date
        except (ValueError, TypeError, OverflowError) as e:
            logger.warning(f"Could not parse date string: '{date_str}'. Error: {e}")
            # Fallback to current time if parsing fails, or return None if preferred
            return datetime.now(timezone.utc)

    def search_local_news(self, location_info: Dict, radius: float, max_results: int, time_range: str) -> List[Dict]:
        city = location_info.get('city', '')
        region = location_info.get('region', '')
        country = location_info.get('country', '')
        time_range_days = self._parse_time_range(time_range)

        user_query = f"Find recent local news from {city}, {region}, {country} within the last {time_range_days} days in a {radius}km radius. Focus on important local events, government updates, and community developments."

        try:
            logger.info(f"Searching for local news with query: {user_query}")
            response = self.client.messages.create(
                model=self.model,
                max_tokens=1024, # As per documentation example
                messages=[{"role": "user", "content": user_query}],
                tools=[{
                    "type": "web_search_20250305",
                    "name": "web_search",
                    "max_uses": 3, # Limiting to 3 searches to be conservative
                    # "allowed_domains": self.allowed_domains, # Temporarily removed for testing
                    "user_location": {
                        "type": "approximate",
                        "city": city,
                        "region": region,
                        "country": location_info.get('country_code', ''),
                        "timezone": location_info.get('timezone', 'UTC')
                    }
                }]
            )
            
            articles = self._process_anthropic_response(response, location_info)
            logger.info(f"Extracted {len(articles)} articles from the response.")
            return articles[:max_results]

        except Exception as e:
            logger.error(f"Error during Anthropic API call or processing: {str(e)}", exc_info=True)
            return self._get_error_placeholder(f"Error during news search: {str(e)}", location_info)

    def _process_anthropic_response(self, response: Any, location_info: Dict) -> List[Dict]:
        articles = []
        raw_search_results = {} # To store raw results by URL for enrichment

        if not response or not response.content:
            logger.warning("Anthropic response or response.content is None.")
            return self._get_error_placeholder("No valid response from news service.", location_info)

        for content_block in response.content:
            if not content_block: continue # Skip if content_block itself is None

            if content_block.type == 'web_search_tool_result':
                block_content_list = getattr(content_block, 'content', None)
                if isinstance(block_content_list, list):
                    for result in block_content_list:
                        if result and result.type == 'web_search_result' and hasattr(result, 'url'):
                            raw_search_results[result.url] = {
                                'title': getattr(result, 'title', 'Untitled'),
                                'content_snippet': getattr(result, 'encrypted_content', ''),
                                'page_age': getattr(result, 'page_age', None)
                            }
            elif content_block.type == 'text':
                citations_list = getattr(content_block, 'citations', None)
                if isinstance(citations_list, list):
                    for citation in citations_list:
                        if citation and citation.type == 'web_search_result_location' and hasattr(citation, 'url'):
                            article_url = citation.url
                            if not any(a['url'] == article_url for a in articles):
                                raw_data = raw_search_results.get(article_url, {})
                                article = {
                                    "title": getattr(citation, 'title', raw_data.get('title', 'Untitled')),
                                    "url": article_url,
                                    "source": self._extract_source(article_url),
                                    "published_date": self._parse_published_date(raw_data.get('page_age')),
                                    "content": getattr(citation, 'cited_text', raw_data.get('content_snippet', ''))[:500] + "...",
                                    "location": location_info,
                                    "relevance_score": 0.85,
                                    "citations": [{
                                        "url": article_url,
                                        "title": getattr(citation, 'title', ''),
                                        "cited_text": getattr(citation, 'cited_text', '')
                                    }]
                                }
                                articles.append(article)
                            else:
                                for art in articles:
                                    if art['url'] == article_url:
                                        existing_citation_urls = [c['url'] for c in art['citations']]
                                        if article_url not in existing_citation_urls:
                                            art['citations'].append({
                                                "url": article_url,
                                                "title": getattr(citation, 'title', ''),
                                                "cited_text": getattr(citation, 'cited_text', '')
                                            })
                                        break
        
        if not articles and raw_search_results:
            logger.info("No articles with citations found, creating from raw search results.")
            for url, data in raw_search_results.items():
                articles.append({
                    "title": data['title'],
                    "url": url,
                    "source": self._extract_source(url),
                    "published_date": self._parse_published_date(data.get('page_age')),
                    "content": data.get('content_snippet', '')[:500] + "...",
                    "location": location_info,
                    "relevance_score": 0.7,
                    "citations": []
                })

        if not articles:
            logger.warning("No news articles could be extracted from the Anthropic response after all processing.")
            return self._get_error_placeholder("No news found for your criteria.", location_info)
            
        return articles

    def _get_error_placeholder(self, message: str, location_info: Dict) -> List[Dict]:
        return [{
            "title": "News Update",
            "url": "",
            "source": "System",
            "published_date": datetime.now(timezone.utc),
            "content": message,
            "location": location_info,
            "relevance_score": 0.1,
            "citations": []
        }]

    def _extract_source(self, url: str) -> str:
        if not url: return "Unknown Source"
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            return domain.replace("www.", "") if domain else "Unknown Source"
        except: return "Unknown Source"

    def _parse_time_range(self, time_range: str) -> int:
        if time_range == "24h": return 1
        elif time_range == "48h": return 2
        elif time_range == "7d": return 7
        # A sensible default if an unexpected value is passed, though LocationRequest has a validator.
        logger.warning(f"Unexpected time_range value: {time_range}, defaulting to 1 day.")
        return 1 