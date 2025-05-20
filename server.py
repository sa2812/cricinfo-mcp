import logging
from dataclasses import dataclass
from typing import Any

import httpx
from bs4 import BeautifulSoup
from fake_useragent import UserAgent
from mcp.server.fastmcp import FastMCP

from constants import SERIES_ARCHIVE

logger = logging.getLogger(__name__)

mcp = FastMCP("Cricinfo")


async def make_cricinfo_request(
    url: str,
    params: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
    timeout: int = 10,
):
    """
    Load a page from Cricinfo
    """
    headers = headers or {
        "User-Agent": UserAgent().chrome,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-GB,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
    }
    async with httpx.AsyncClient(cookies=httpx.Cookies()) as client:
        try:
            response = await client.get(
                url,
                headers=headers,
                timeout=timeout,
                follow_redirects=True,
                params=params,
            )
            logger.info(
                "Request to %s returned status code %s", url, response.status_code
            )
            response.raise_for_status()
            return response.text
        except Exception:
            logger.exception("Failed to retrieve page from Cricinfo: %s", url)


def to_soup(content: str):
    """
    Convert HTML content to BeautifulSoup object
    """
    return BeautifulSoup(content, "html.parser")


@dataclass
class Series:
    """
    Data class for storing cricket series information
    """

    name: str
    link: str
    date_location: str


@mcp.tool(
    name="Get Series By Year",
    description="Get the full list of internationally-recognised cricket series for a given year",
)
async def get_series_by_year(year: int) -> list[Series]:
    """
    Get the full list of internationally-recognised cricket series for a given year

    Args:
        year (int): The year to get the series for.
    """
    logger.info("Fetching series archive for year %s", year)
    year_str = str(year)
    if not len(year_str) == 4:
        raise ValueError("Year must be a 4-digit number.")

    years = [
        f"{year-1}%2F{year_str[2:]}",
        year_str,
        f"{year_str}%2F{str(year+1)[2:]}",
    ]

    soup_pot = []

    for i in years:
        url = SERIES_ARCHIVE + f"season={i};view=season"
        try:
            content = await make_cricinfo_request(url)
            if content:
                soup_pot.append(to_soup(content))
        except Exception:
            logger.exception("Failed to retrieve series archive page for year %s", i)

    series = []

    for soup in soup_pot:
        if not soup:
            continue

        series_summaries = soup.find_all("section", class_="brief-summary")
        for summary in series_summaries:
            try:
                teams_div = summary.find("div", class_="teams")
                date_location_div = summary.find("div", class_="date-location")
            except Exception:
                logger.exception(
                    "Failed to parse series archive page for year %s", year
                )
                continue

            try:
                series.append(
                    Series(
                        name=teams_div.find("a").text.strip(),
                        link=teams_div.find("a")["href"],
                        date_location=date_location_div.text.strip(),
                    )
                )
            except Exception:
                logger.exception(
                    "Failed to parse series archive page for year %s", year
                )

    return series


if __name__ == "__main__":
    logger.info("Starting Cricinfo MCP server")
    mcp.run(transport="stdio")
