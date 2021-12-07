import requests
import re

from typing import Optional, List, Dict

from .endpoints import *
from .errors import CrunchyrollError

# Universal Authorization to access Crunchyroll Beta API
AUTHORIZATION = "Basic aHJobzlxM2F3dnNrMjJ1LXRzNWE6cHROOURteXRBU2Z6QjZvbXVsSzh6cUxzYTczVE1TY1k="

class Crunchyroll():
    """Crunchyroll BETA Client
    
    Parameters:
        locale (``str``, optional):
            The language to use in Crunchyroll
            E.g.: en-US, it-IT...
            Default to en-US
    """

    def __init__(self, locale: str="en-US") -> None:
        self.locale = locale
        self.config = dict()
        self.api_headers = {
            "User-Agent": "Crunchyroll/3.10.0 Android/6.0 okhttp/4.9.1",
            "Content-Type": "application/x-www-form-urlencoded"
        }

    def _make_request(self, method: str, url: str, headers: Dict=dict(), params=None, data=None) -> Optional[Dict]:
        headers.update(self.api_headers)
        r = requests.request(
            method,
            url,
            headers=headers,
            params=params,
            data=data
        )
        code = r.status_code
        r_json = r.json()
        if "error" in r_json:
            error_code = r_json.get("error")
            if error_code == "invalid_grant":
                raise CrunchyrollError(f"[{code}] Invalid login credentials.")
        elif "message" in r_json and "code" in r_json:
            message = r_json.get("message")
            raise CrunchyrollError(f"[{code}] Error occured: {message}")
        if code != 200:
            raise CrunchyrollError(f"[{code}] {r.text}")
        return r_json

    def login(self, username: str, password: str) -> Optional[bool]:
        """Login to Crunchyroll

        Parameters:
            username (``str``):
                Email or username of the account
            password (``str``):
                Password of the account

        Returns:
            ``bool``: On success, True is returned
        """
        headers = {"Authorization": AUTHORIZATION}
        r = self._make_request(
            method="POST",
            url=TOKEN_ENDPOINT,
            headers=headers,
            data = {
                "username": username,
                "password": password,
                "grant_type": "password",
                "scope": "offline_access",
            }
        )
        access_token = r["access_token"]
        token_type = r["token_type"]
        authorization = {"Authorization": f"{token_type} {access_token}"}
        self.config.update(r)
        self.api_headers.update(authorization)
        r = self._make_request(method="GET", url=INDEX_ENDPOINT)
        self.config.update(r)
        r = self._make_request(method="GET", url=PROFILE_ENDPOINT)
        self.config.update(r)
        return True

    def search(self, query: str, n: int=6) -> Optional[List]:
        """Search series

        Parameters:
            query (``str``):
                Query to search
            n (``int``, optional):
                Number of results to return
                Default to 6

        Returns:
            ``List``: On success, list is returned
        """
        r = self._make_request(
            method="GET",
            url=SEARCH_ENDPOINT,
            params = {
                "q": query,
                "n": str(n),
                "locale": self.locale
            }
        )
        return r["items"]

    def get_series(self, series_id: str) -> Optional[List]:
        """Get info about a series

        Parameters:
            series_id (``str``):
                ID of the series

        Returns:
            ``List``: On success, list is returned
        """
        r = self._make_request(
            method="GET",
            url=SERIES_ENDPOINT.format(self.config["cms"]["bucket"], series_id),
            params = {
                "Policy": self.config["cms"]["policy"],
                "Signature": self.config["cms"]["signature"],
                "Key-Pair-Id": self.config["cms"]["key_pair_id"],
                "locale": self.locale
            }
        )
        #return self.mkobj(r, Series)
        return r
        
    def get_seasons(self, series_id: str) -> Optional[List]:
        """Get seasons of a series

        Parameters:
            series_id (``str``):
                ID of the series

        Returns:
            ``List``: On success, list is returned
        """
        r = self._make_request(
            method="GET",
            url=SEASONS_ENDPOINT.format(self.config["cms"]["bucket"]),
            params = {
                "series_id": series_id,
                "Policy": self.config["cms"]["policy"],
                "Signature": self.config["cms"]["signature"],
                "Key-Pair-Id": self.config["cms"]["key_pair_id"],
                "locale": self.locale
            }
        )
        return r["items"]

    def get_episodes(self, season_id: str) -> Optional[List]:
        """Get episodes of a series (from season)

        Parameters:
            season_id (``str``):
                ID of a season

        Returns:
            ``List``: On success, list is returned
        """
        r = self._make_request(
            method="GET",
            url=EPISODES_ENDPOINT.format(self.config["cms"]["bucket"]),
            params = {
                "season_id": season_id,
                "Policy": self.config["cms"]["policy"],
                "Signature": self.config["cms"]["signature"],
                "Key-Pair-Id": self.config["cms"]["key_pair_id"],
                "locale": self.locale
            }
        )
        return r["items"]

    def get_streams(self, episode: Dict) -> Optional[Dict]:
        """Get streams from an episode

        Parameters:
            episode (``Dict``):
                Pass one of the items that ``get_episodes()`` returns

        Returns:
            ``Dict``: On success, dictionary is returned
        """
        stream_id = re.search(r"videos\/(.+?)\/streams",
            episode["__links__"]["streams"]["href"]
        ).group(1)
        r = self._make_request(
            method="GET",
            url=STREAMS_ENDPOINT.format(self.config["cms"]["bucket"], stream_id),
            params = {
                "Policy": self.config["cms"]["policy"],
                "Signature": self.config["cms"]["signature"],
                "Key-Pair-Id": self.config["cms"]["key_pair_id"],
                "locale": self.locale
            }
        )
        return r

    def get_similar(self, series_id: str, n: int=6) -> Optional[List]:
        """Get similar series

        Parameters:
            series_id (``str``):
                ID of the series
            n (``int``, optional):
                Number of results to return
                Default to 6

        Returns:
            ``List``: On success, list is returned
        """
        r = self._make_request(
            method="GET",
            url=SIMILAR_ENDPOINT.format(self.config["account_id"]),
            params = {
                "guid": series_id,
                "n": str(n),
                "locale": self.locale
            }
        )
        return r["items"]

    def news_feed(self, n: int=6) -> Optional[Dict]:
        """Get news feed

        Parameters:
            n (``int``, optional):
                Number of results to return
                Default to 6

        Returns:
            ``Dict``: On success, dictionary is returned
        """
        r = self._make_request(
            method="GET",
            url=NEWSFEED_ENDPOINT,
            params = {
                "n": str(n),
                "locale": self.locale
            }
        )
        return r