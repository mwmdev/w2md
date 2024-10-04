# `w2md` Web to Markdown Scraper

`w2md` scrapes specific content from a list of URLs and converts it into a Markdown file. It is useful for extracting documentation or content from web pages in a format that can be easily used by other tools, such as Language Models (LLMs).

## Features
- Scrape content from a list of URLs (provided in a text file).
- Select specific HTML elements by class, ID, or tag name.
- Exclude certain elements within the target content.
- Convert the selected content to Markdown.
- Save the final concatenated Markdown content to a file.

## Requirements
- Python 3.x
- The following Python libraries:
  - `requests`
  - `beautifulsoup4`
  - `markdownify`
  - `rich`

You can install all required dependencies using `pip`:

```sh
pip install -r requirements.txt
```

## Usage
The script takes several command-line arguments to define what content to scrape and how to process it.

### Command-line Arguments
- `--urls` or `-u`: The path to the file containing the URLs, one per line. (Default: `urls`)
- `--target` or `-t`: The class, ID, or HTML element to scrape content from (e.g., `.content`, `#main`, `div`). (Required)
- `--exclude` or `-x`: A list of classes, IDs, or HTML elements to exclude from the scraped content. Supports multiple selectors.
- `--output` or `-o`: The name of the output Markdown file. (Default: `output.md`)

### Example Usage
```sh
python w2md.py -u urls.txt -t ".content" -x ".social-share,#sidebar" -o documentation.md
```
This command scrapes the content from URLs listed in `urls.txt`, targeting elements with class `.content`, excluding elements with class `.social-share` and ID `#sidebar`, and saving the output to `documentation.md`.

## Notes
- The script waits 3 seconds between each request to prevent overwhelming the servers being scraped.
- Make sure to respect the terms of service of any website you're scraping, as automated scraping may be prohibited.