import requests
from bs4 import BeautifulSoup
from dateutil import parser
import json
from datetime import datetime
from typing import TypedDict
import csv


__all__ = (
    "AfadEarthquakeScraper",
    "AfadDepremScraper",
    "EarthquakeRecord",
)


class EarthquakeRecord(TypedDict):
    id: str
    datetime: str
    date: str
    time: str
    latitude: str
    longitude: str
    depth: str
    type: str
    magnitude: str
    region: str


class AfadEarthquakeScraper:
    """
    Scrapes the last 100 earthquakes from AFAD's website.
    """

    def __init__(self, url=None):
        self.url = url or "https://deprem.afad.gov.tr/last-earthquakes.html"
        self.session = requests.Session()

    def _get_html_table(self) -> bytes:
        response = self.session.get(self.url)
        return response.content

    def _get_soup(self, html: str | bytes) -> BeautifulSoup:
        return BeautifulSoup(html, "html.parser")

    def scrape_table(self) -> list[EarthquakeRecord]:
        """
        Get table values from AFAD's website as a list of records (dicts).

        Raises:
            ValueError: if the table was not found because of a change
                in the website. or if the table data is empty.

        Returns:
            list[EarthquakeRecord]: a list of 100 earthquake records.
        """
        soup = self._get_soup(self._get_html_table())
        table = soup.find("table", {"class": "content-table"})
        if not table:
            raise ValueError("Table was not found. Check the URL or file a bug.")

        results = []
        for tr in table.tbody.find_all("tr"):
            tds = tr.find_all("td")
            date_time = parser.parse(tds[0].text)
            results.append(
                {
                    "id": tds[-1].text,
                    "datetime": date_time.isoformat(),
                    "date": date_time.date().isoformat(),
                    "time": str(date_time.time()),
                    "latitude": tds[1].text,
                    "longitude": tds[2].text,
                    "depth": tds[3].text,
                    "type": tds[4].text,
                    "magnitude": tds[5].text,
                    "region": tds[6].text,
                }
            )
        return sorted(
            results,
            key=lambda r: r["datetime"],
            reverse=True,
        )

    def export_json(self) -> str:
        """
        Export the table data as a JSON string.
        """
        return json.dumps(self.scrape_table(), ensure_ascii=False)

    def export_csv(self, file_name: str = None) -> None:
        """
        Export the table data as a CSV file.

        Args:
            file_name (str, optional): The CSV file name. Defaults to None, a
                timestamped file name.
        """
        table_data = self.scrape_table()
        sample_keys = table_data[0].keys()

        with open(
            file_name or f"earthquakes-export-{datetime.now().isoformat()}.csv", "w"
        ) as f:
            writer = csv.DictWriter(f, fieldnames=sample_keys)
            writer.writeheader()
            writer.writerows(table_data)


AfadDepremScraper = AfadEarthquakeScraper


def main() -> None:
    scraper = AfadEarthquakeScraper()
    from pprint import pprint as pp

    pp(scraper.scrape_table()[0])


if __name__ == "__main__":
    raise SystemExit(main())
