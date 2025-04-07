"""
EnlightenAI - Fetch Web Node

This module contains the FetchWebNode class, which is responsible for
fetching content from web pages using crawl4ai and storing it in the shared context.
"""

import asyncio

from crawl4ai import AsyncWebCrawler, BrowserConfig, CacheMode, CrawlerRunConfig

from nodes import Node


class FetchWebNode(Node):
    """Node for fetching content from web pages using crawl4ai."""

    def process(self, context):
        """Fetch content from web pages specified in the context.

        Args:
            context (dict): The shared context dictionary containing:
                - web_url: The web page URL to crawl
                - verbose: Whether to print verbose output

        Returns:
            None: The context is updated directly with the fetched content.
        """
        web_url = context.get("web_url")
        verbose = context.get("verbose", False)

        if not web_url:
            if verbose:
                print("No web_url provided, skipping web crawling")
            return None

        if verbose:
            print(f"Fetching web content from: {web_url}")

        # Configure the browser
        browser_config = BrowserConfig(headless=True, verbose=verbose)

        # Configure the crawler
        run_config = CrawlerRunConfig(cache_mode=CacheMode.ENABLED)

        # Run the crawler
        result = asyncio.run(self._run_crawler(web_url, browser_config, run_config))

        # Store the result in the context
        context["web_content"] = {
            "markdown": result.markdown.raw_markdown,
            "fit_markdown": result.markdown.fit_markdown,
            "html": result.html,
            "cleaned_html": result.cleaned_html,
            "url": result.url,
            "metadata": result.metadata or {},
        }

        # Add title from metadata if available
        if result.metadata and "title" in result.metadata:
            context["web_content"]["title"] = result.metadata["title"]

        if verbose:
            print(f"Successfully fetched content from {web_url}")
            print(f"Markdown length: {len(result.markdown.raw_markdown)}")

        # Return None as we've updated the context directly
        return None

    async def _run_crawler(self, url, browser_config, run_config):
        """Run the crawler asynchronously.

        Args:
            url (str): The URL to crawl
            browser_config (BrowserConfig): Browser configuration
            run_config (CrawlerRunConfig): Crawler run configuration

        Returns:
            CrawlResult: The result of the crawl
        """
        async with AsyncWebCrawler(config=browser_config) as crawler:
            result = await crawler.arun(url=url, config=run_config)
            return result
