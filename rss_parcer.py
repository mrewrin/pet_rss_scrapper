import logging
import requests
import xml.etree.ElementTree as eT
from argparse import ArgumentParser
from typing import List, Optional, Sequence, Union
import json as j
import html


class UnhandledException(Exception):
    pass


def rss_parser(
    xml: str,
    limit: Optional[int] = None,
    json: bool = False,
) -> Union[List[str], str]:
    """
    RSS parser.

    Args:
        xml: XML document as a string.
        limit: Number of the news to return. if None, returns all news.
        json: If True, format output as JSON.

    Returns:
        List of strings or JSON string.
    """
    try:
        root = eT.fromstring(xml)
        channel = root.find('channel')

        if channel is None:
            raise ValueError("Invalid RSS format: missing channel element")

        # Extract feed information
        feed_info = {
            'Feed': channel.findtext('title') or '',
            'Link': channel.findtext('link') or '',
            'Description': channel.findtext('description') or '',
        }

        # Extract optional fields from channel
        for field in ['lastBuildDate', 'pubDate', 'language', 'managingEditor']:
            value = channel.findtext(field)
            if value:
                feed_info[field.capitalize()] = value

        # Extract categories if available
        categories = ', '.join([category.text for category in channel.findall('category')])
        if categories:
            feed_info['Categories'] = categories

        # Extract item information
        items = []
        for item in channel.findall('item'):
            item_info = {
                'Title': item.findtext('title') or '',
                'Author': item.findtext('author') or '',
                'PubDate': item.findtext('pubDate') or '',
                'Link': item.findtext('link') or '',
                'Category': item.findtext('category') or '',
                'Description': item.findtext('description') or ''
            }
            items.append(item_info)

        # Apply limit if provided
        if limit is not None:
            items = items[:limit]

        # Format output as JSON if required
        if json:
            output = {
                'title': feed_info['Feed'],
                'link': feed_info['Link'],
                'description': feed_info['Description'],
                'items': items
            }
            return j.dumps(output, indent=2)
        else:
            # Format output as text
            output = [f"Feed: {html.unescape(feed_info['Feed'])}", f"Link: {feed_info['Link']}",
                      f"Description: {html.unescape(feed_info['Description'])}"]

            for field in ['LastBuildDate', 'PubDate', 'Language', 'ManagingEditor', 'Categories']:
                if field in feed_info:
                    output.append(f"{field}: {feed_info[field]}")

            for item in items:
                output.append(f"\nTitle: {html.unescape(item['Title'])}")
                output.append(f"Author: {item['Author']}")
                output.append(f"PubDate: {item['PubDate']}")
                output.append(f"Link: {item['Link']}")
                output.append(f"Category: {item['Category']}")
                output.append(f"Description: {html.unescape(item['Description'])}")

            return output

    except Exception as e:
        raise UnhandledException(e)


def main(argv: Optional[Sequence] = None) -> int:
    """
    The main function of your task.
    """
    # Define command-line arguments
    parser = ArgumentParser(
        prog="rss_reader",
        description="Pure Python command-line RSS reader.",
    )
    parser.add_argument("source", help="RSS URL", type=str, nargs="?")
    parser.add_argument(
        "--json", help="Print result as JSON in stdout", action="store_true"
    )
    parser.add_argument(
        "--limit", help="Limit news topics if this parameter provided", type=int
    )

    args = parser.parse_args(argv)

    # Validate RSS URL
    if not args.source:
        parser.error("Please provide a valid RSS URL.")
        return 1

    try:
        # Fetch RSS feed
        response = requests.get(args.source)
        response.raise_for_status()
        xml = response.text
    except requests.RequestException as e:
        # Handle request error
        logging.error(f"Error while fetching RSS feed: {e}")
        return 1

    try:
        # Parse and print RSS feed
        output = rss_parser(xml, args.limit, args.json)
        if args.json:
            print(output)
        else:
            print("\n".join(output))
        return 0
    except Exception as e:
        # Handle unhandled exception
        logging.error(f"Unhandled exception: {e}")
        return 1


if __name__ == "__main__":
    main()
