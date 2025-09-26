from pathlib import Path
from mcp.server.fastmcp import FastMCP
from fastapi import FastAPI
from fastapi.responses import FileResponse

from custom_server.ainews import DEFAULT_AINEWS_RSS_URL, fetch_ainews_rss, format_ainews_story, parse_ainews_rss
from custom_server.hackernews import DEFAULT_HN_RSS_URL, fetch_hn_rss, format_hn_story, parse_hn_rss
from custom_server.techcrunch import DEFAULT_TC_RSS_URL, fetch_tc_rss, format_tc_story, parse_tc_rss
from custom_server.wired import DEFAULT_WIRED_RSS_URL, fetch_wired_rss, format_wired_story, parse_wired_rss
from custom_server.wsj import DEFAULT_WSJ_RSS_URL, fetch_wsj_rss, format_wsj_story, parse_wsj_rss

STATIC_DIR = Path(__file__).parent / "static"

# Create an MCP server
mcp = FastMCP("Custom MCP Server on Databricks Apps")

@mcp.tool()
async def get_hackernews_stories(
    feed_url: str = DEFAULT_HN_RSS_URL, count: int = 30
) -> str:
    """Get top stories from Hacker News.

    Args:
        feed_url: URL of the RSS feed to use (default: Hacker News)
        count: Number of stories to return (default: 5)
    """
    rss_content = await fetch_hn_rss(feed_url)
    if rss_content.startswith("Error"):
        return rss_content

    stories = parse_hn_rss(rss_content)

    # Limit to requested count
    stories = stories[: min(count, len(stories))]

    if not stories:
        return "No stories found."

    formatted_stories = [format_hn_story(story) for story in stories]
    return "\n---\n".join(formatted_stories)


@mcp.tool()
async def get_wallstreetjournal_stories(
    feed_url: str = DEFAULT_WSJ_RSS_URL, count: int = 30
) -> str:
    """Get stories from Wall Street Journal.

    Args:
        feed_url: URL of the WSJ RSS feed to use
        count: Number of stories to return (default: 5)
    """
    # Fetch the content
    rss_content = await fetch_wsj_rss(feed_url)
    if rss_content.startswith("Error"):
        return rss_content

    stories = parse_wsj_rss(rss_content)

    # Check for errors in parsing
    if stories and "error" in stories[0]:
        return stories[0]["error"]

    # Limit to requested count
    stories = stories[: min(count, len(stories))]

    if not stories:
        return "No stories found."

    formatted_stories = [format_wsj_story(story) for story in stories]
    return "\n---\n".join(formatted_stories)


@mcp.tool()
async def get_techcrunch_stories(
    feed_url: str = DEFAULT_TC_RSS_URL, count: int = 30
) -> str:
    """Get stories from TechCrunch.

    Args:
        feed_url: URL of the TechCrunch RSS feed to use
        count: Number of stories to return (default: 30)
    """
    # Fetch the content
    rss_content = await fetch_tc_rss(feed_url)
    if rss_content.startswith("Error"):
        return rss_content

    stories = parse_tc_rss(rss_content)

    # Check for errors in parsing
    if stories and "error" in stories[0]:
        return stories[0]["error"]

    # Limit to requested count
    stories = stories[: min(count, len(stories))]

    if not stories:
        return "No stories found."

    formatted_stories = [format_tc_story(story) for story in stories]
    return "\n---\n".join(formatted_stories)


@mcp.tool()
async def get_ainews_latest(feed_url: str = DEFAULT_AINEWS_RSS_URL) -> str:
    """Get the latest story from AI News.

    Args:
        feed_url: URL of the AI News RSS feed to use (default: AI News)
    """
    # Fetch the content
    rss_content = await fetch_ainews_rss(feed_url)
    if rss_content.startswith("Error"):
        return rss_content

    stories = parse_ainews_rss(rss_content)

    # Check for errors in parsing
    if stories and "error" in stories[0]:
        return stories[0]["error"]

    if not stories:
        return "No stories found."

    # Only format the latest story
    return format_ainews_story(stories[0])


@mcp.tool()
async def get_wired_stories(
    feed_url: str = DEFAULT_WIRED_RSS_URL, count: int = 30
) -> str:
    """Get AI stories from Wired.

    Args:
        feed_url: URL of the Wired RSS feed to use (default: Wired AI feed)
        count: Number of stories to return (default: 30)
    """
    # Fetch the content
    rss_content = await fetch_wired_rss(feed_url)
    if rss_content.startswith("Error"):
        return rss_content

    stories = parse_wired_rss(rss_content)

    # Check for errors in parsing
    if stories and "error" in stories[0]:
        return stories[0]["error"]

    # Limit to requested count
    stories = stories[: min(count, len(stories))]

    if not stories:
        return "No stories found."

    formatted_stories = [format_wired_story(story) for story in stories]
    return "\n---\n".join(formatted_stories)


# Add an addition tool
@mcp.tool()
def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b


# Add a dynamic greeting resource
@mcp.resource("greeting://{name}")
def get_greeting(name: str) -> str:
    """Get a personalized greeting"""
    return f"Hello, {name}!"


mcp_app = mcp.streamable_http_app()


app = FastAPI(
    lifespan=lambda _: mcp.session_manager.run(),
)


# Add info endpoint
@app.get("/", include_in_schema=False)
async def serve_info():
    return {
        "server": "News MCP Server",
        "tools": ["hackernews", "techcrunch", "wired", "ainews", "wsj"],
        "mcp_protocol": True,
        "mcp_endpoint": "/mcp/",
        "test_endpoints": [
            "/test/hackernews?count=3",
            "/test/techcrunch?count=3",
            "/test/wired?count=3",
            "/test/ainews",
            "/test/wsj?count=3"
        ]
    }

# Add simple test endpoints for easy browser testing
@app.get("/test/hackernews")
async def test_hackernews(count: int = 5):
    stories = await get_hackernews_stories(count=count)
    return {"source": "Hacker News", "count": count, "stories": stories}

@app.get("/", include_in_schema=False)
async def serve_index():
    return FileResponse(STATIC_DIR / "index.html")


app.mount("/", mcp_app)
