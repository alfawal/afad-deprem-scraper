import csv
import json
from datetime import datetime
from pathlib import Path
from typing import Literal, Self, TypedDict

import requests
from bs4 import BeautifulSoup
from dateutil import parser

__all__ = (
    "AfadEarthquakeScraper",
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

    def __init__(self, url: str = None):
        self._url: str = url or "https://deprem.afad.gov.tr/last-earthquakes.html"
        self._session: requests.Session = requests.Session()
        self._data: list[EarthquakeRecord] | None = None

    @property
    def results(self) -> list[EarthquakeRecord] | list:
        if self._data is None:
            raise ValueError("No data found. Run scrape_table() first.")
        return self._data

    @property
    def length(self) -> int:
        return len(self.results)

    def _get_html_table(self) -> bytes:
        response: requests.Response = self._session.get(self._url)
        if not response.ok:
            raise requests.HTTPError(
                f"Non-success status code returned: {response.status_code}"
                "\nCheck the URL or file a bug."
            )
        return response.content

    def _get_soup(self, html: str | bytes) -> BeautifulSoup:
        return BeautifulSoup(html, "html.parser")

    def _prepare_file_path(self, file_type: str, file_name: str, directory: str) -> str:
        file_path = ""
        if directory:
            file_path += directory + "/" if not directory.endswith("/") else directory

            # Create the directory if it doesn't exist
            Path(file_path).mkdir(parents=True, exist_ok=True)

        if file_name:
            file_path += (
                file_name
                if file_name.endswith(f".{file_type}")
                else file_name + f".{file_type}"
            )
        else:
            file_path += (
                f"afad-earthquakes-export-{datetime.now().isoformat()}.{file_type}"
            )

        return file_path

    def scrape_table(self) -> Self:
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
            raise ValueError("Data table was not found. Check the URL or file a bug.")

        self._data = []
        for tr in table.tbody.find_all("tr"):
            tds = tr.find_all("td")
            date_time = parser.parse(tds[0].text)
            self._data.append(
                # TODO: Refactor the mappings, reading the values dynamically
                #  from the table headers in some way.
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

        self._data.sort(key=lambda record: record["datetime"], reverse=True)
        return self

    def export_json(
        self,
        *,
        type: Literal["file", "string"] = "file",
        file_name: str = "",
        directory: str = "",
    ) -> str | None:
        """
        Export the table data as a JSON string.

        Args:
            type (Literal["file", "string"], optional): The type of the output.
                Defaults to "file".
            file_name (str, optional): The JSON file name. Defaults to a
                timestamped file name. Only used if type is "file".
            directory (str, optional): The directory to write the file to.
                Defaults to the current directory. Only used if type is "file".

        Raises:
            ValueError: if the type is not "file" or "string".

        Returns:
            str | None: the JSON string if type is "string", None otherwise.
        """
        if type not in ("file", "string"):
            raise ValueError("type must be either 'file' or 'string'.")

        if type == "string":
            return json.dumps(self.results, ensure_ascii=False)

        file_path = self._prepare_file_path("json", file_name, directory)
        with open(file_path, "w") as f:
            json.dump(self.results, f, ensure_ascii=False)

        print(f"Exported to {file_path!r}")

    def export_csv(self, *, file_name: str = "", directory: str = "") -> None:
        """
        Export the table data as a CSV file.

        Args:
            file_name (str, optional): The CSV file name. Defaults to a
                timestamped file name.
            directory (str, optional): The directory to write the file to.
                Defaults to the current directory.

        Returns:
            None
        """
        if not self.results:
            raise ValueError("Cannot export empty data.")

        file_path = self._prepare_file_path("csv", file_name, directory)
        columns = self.results[0].keys()
        with open(file_path, "w") as f:
            writer = csv.DictWriter(f, fieldnames=columns)
            writer.writeheader()
            writer.writerows(self.results)

        print(f"Exported to {file_path!r}")


def main() -> None:
    from pprint import pprint as pp

    scraper = AfadEarthquakeScraper()
    table = scraper.scrape_table()

    # Results as a list of dicts
    results = table.results
    pp(results)

    # Number of results
    results_length = table.length
    pp(results_length)

    # export to JSON string
    json_string = table.export_json(type="string")
    pp(json_string)

    # export to JSON file
    table.export_json(
        type="file",
        file_name="afad-earthquakes.json",
        directory="export_examples/json",
    )

    # export to CSV file
    table.export_csv(
        file_name="afad-earthquakes.csv",
        directory="export_examples/csv",
    )


if __name__ == "__main__":
    raise SystemExit(main())
