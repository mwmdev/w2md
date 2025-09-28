import requests
from bs4 import BeautifulSoup
import markdownify
import argparse
import os
import time
import re
from dataclasses import dataclass
from typing import Iterable
from rich import print
from rich.progress import track
from rich.table import Table
from rich.console import Console


@dataclass
class ScrapeResult:
    url: str
    html_content: str
    matched: bool
    excluded_count: int
    error: str | None = None


def scrape_content(url, target_selector, exclude_selectors):
    try:
        # Set up headers with a common User-Agent to avoid being blocked by some sites
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        # Send GET request to the URL
        response = requests.get(url, headers=headers)
        # Handle specific HTTP status codes to provide more informative error messages
        if response.status_code == 404:
            print(f"[red]Error 404: URL '{url}' not found.[/red]")
            return ScrapeResult(url=url, html_content="", matched=False, excluded_count=0, error="HTTP 404")
        elif response.status_code == 500:
            print(f"[red]Error 500: Server error at URL '{url}'.[/red]")
            return ScrapeResult(url=url, html_content="", matched=False, excluded_count=0, error="HTTP 500")
        elif response.status_code != 200:
            print(f"[red]Error {response.status_code}: Failed to fetch URL '{url}'.[/red]")
            return ScrapeResult(url=url, html_content="", matched=False, excluded_count=0, error=f"HTTP {response.status_code}")

        soup = BeautifulSoup(response.content, 'html.parser')

        # Determine if the target selector is an ID, a class, or a general HTML element
        if target_selector.startswith("#"):
            element = soup.find(id=target_selector[1:])
        elif target_selector.startswith("."):
            element = soup.find(class_=target_selector[1:])
        else:
            element = soup.find(target_selector)

        excluded_count = 0

        # If the element was found, process it
        if element:
            # Remove excluded elements from the target using advanced CSS selectors
            for exclude_selector in exclude_selectors:
                exclude_elements = element.select(exclude_selector)  # Find all matching elements to exclude
                excluded_count += len(exclude_elements)
                for exclude_element in exclude_elements:
                    exclude_element.decompose()  # Remove the element from the parsed HTML tree

            return ScrapeResult(
                url=url,
                html_content=str(element),
                matched=True,
                excluded_count=excluded_count,
            )
        else:
            # Print a warning if the target element was not found
            print(f"[yellow]Warning: No content found for selector '{target_selector}' in URL: {url}[/yellow]")
            return ScrapeResult(url=url, html_content="", matched=False, excluded_count=0)

    except requests.RequestException as e:
        # Print an error message if the request fails
        print(f"[red]Error fetching URL '{url}': {e}[/red]")
        return ScrapeResult(url=url, html_content="", matched=False, excluded_count=0, error=str(e))


def convert_to_markdown(html_content):
    # Remove zero-width space (ZWSP) characters from the HTML content
    html_content = re.sub(r'\u200b', '', html_content)
    # Convert HTML to Markdown using markdownify
    markdown_content = markdownify.markdownify(html_content, heading_style="ATX")

    # Remove Markdown hyperlinks, keeping only the link text using a more robust approach
    from markdownify import MarkdownConverter
    class CustomMarkdownConverter(MarkdownConverter):
        def convert_a(self, el, text, convert_as_inline):
            # Override the link conversion to keep only the link text
            return text

    markdown_content = CustomMarkdownConverter().convert(html_content)

    # Remove escaped underscores in the Markdown content
    markdown_content = markdown_content.replace('\_', '_')

    # Make sure titles are on their own line
    markdown_content = re.sub(r'(\w)(#+)', r'\1\n\2', markdown_content)

    return markdown_content


def display_dry_run_report(results: Iterable[ScrapeResult], target_selector: str):
    table = Table(title=f"Dry Run Summary for selector '{target_selector}'")
    table.add_column("URL", overflow="fold")
    table.add_column("Matched", justify="center")
    table.add_column("Excluded Elements", justify="right")
    table.add_column("Notes", overflow="fold")

    for result in results:
        notes = []
        if result.error:
            notes.append(result.error)
        elif not result.matched:
            notes.append("No match")

        table.add_row(
            result.url,
            "✅" if result.matched else "❌",
            str(result.excluded_count),
            ", ".join(notes) if notes else "",
        )

    console = Console()
    console.print(table)


def main():
    # Set up argument parser to get command-line arguments
    parser = argparse.ArgumentParser(description='Scrape content from URLs and save as Markdown.')
    parser.add_argument('--urls', '-u', type=str, default='urls',
                        help='Path to the file containing the URLs, one per line.')
    parser.add_argument('--target', '-t', type=str, required=True,
                        help='Class, ID, or HTML element to get the content from (e.g., ".content", "#main", or "div").')
    parser.add_argument('--exclude', '-x', type=str, nargs='*', default=[],
                        help='List of classes, IDs, or HTML elements to exclude from the target content (supports CSS selectors).')
    parser.add_argument('--output', '-o', type=str, default='output.md', help='Name of the output Markdown file.')
    parser.add_argument('--dry-run', action='store_true', help='Preview matches without writing output.')

    args = parser.parse_args()

    # Read URLs from the provided file
    if not os.path.exists(args.urls):
        # Print an error if the URL file does not exist
        print(f"[red]Error: The file '{args.urls}' does not exist.[/red]")
        return

    with open(args.urls, 'r') as f:
        # Read all URLs, stripping out any empty lines
        urls = [line.strip() for line in f if line.strip()]

    if not urls:
        # Print an error if no URLs were found in the file
        print("[red]Error: No URLs found in the file.[/red]")
        return

    # Scrape and convert content from each URL
    all_markdown_content = []
    results: list[ScrapeResult] = []

    for url in track(urls, description="[cyan]Scraping URLs...[/cyan]"):
        # Scrape HTML content from the given URL and target selector
        result = scrape_content(url, args.target, args.exclude)
        results.append(result)

        if result.matched and not args.dry_run:
            # Convert the HTML content to Markdown
            markdown_content = convert_to_markdown(result.html_content)
            # Append the converted content to the list
            all_markdown_content.append(markdown_content)

        # Rate limiting of 3 seconds between requests to avoid overwhelming the server
        time.sleep(3)

    if args.dry_run:
        display_dry_run_report(results, args.target)
        return

    # Save the concatenated Markdown content to the output file if there's content
    if all_markdown_content:
        with open(args.output, 'w') as f:
            f.write('\n\n'.join(all_markdown_content))
        # Print a success message when the file is saved
        print(f"[green]Markdown content saved to '{args.output}'[/green]")
    else:
        print("[yellow]No content to save. Output file not created.[/yellow]")


if __name__ == "__main__":
    main()