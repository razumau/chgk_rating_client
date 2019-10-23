from typing import Dict, List, Union
import json
import os
import glob
import logging

import requests
import logzero
import redis


logger = logzero.setup_logger(level=logging.INFO)


def connect_to_redis(host: str, port: int = 6379):
    logger.debug(f"Creating connection to redis at {host}:{port}")
    redis_client = redis.Redis(host, port)
    # Redis constructor doesn‘t check connection, so we make a request to check it
    redis_client.echo(42)
    return redis_client


class Rating:
    _url = "https://rating.chgk.info/api"
    _prefix = "chgk_rating_"
    _redis: redis.Redis

    def __init__(
        self, file_cache: bool = None, redis_host: str = None, redis_port: int = 6379
    ):
        self._file_cache = file_cache
        if file_cache:
            os.makedirs("cache", exist_ok=True)

        if redis_host:
            self._redis_cache = True
            try:
                self._redis = connect_to_redis(redis_host, redis_port)
            except redis.ConnectionError:
                logger.error(f"Couldn’t connect to redis at {redis_host}:{redis_port}")
                raise ValueError(
                    f"Couldn’t connect to redis at {redis_host}:{redis_port}"
                )
        else:
            self._redis_cache = False
            self._redis = None

        self._cache = self._file_cache or self._redis_cache

    def _check_cache(self, query: str):
        if self._redis_cache:
            logger.debug(f"Querying redis cache for {query}")
            result = self._redis.get(f"{self._prefix}{query}")
            if not result:
                logger.debug(f"No redis cache for {query}")
                return None

            return json.loads(result)

        if self._file_cache:
            logger.debug(f"Checking local cache for {query}")
            try:
                cache_file = open(f"cache/{query.replace('/', '_')}.json")
                return json.load(cache_file)
            except FileNotFoundError:
                logger.debug(f"No cache at {query.replace('/', '_')}.json")
                return None
            except (json.JSONDecodeError, Exception) as e:
                logger.debug(f"Failed parsing or loading local cache for {query}")
                logger.debug(e)
                return None

    def _save_to_cache(self, query: str, data) -> None:
        if self._redis:
            self._redis.set(f"{self._prefix}{query}", json.dumps(data))

        if self._file_cache:
            filename = f"cache/{query.replace('/', '_')}.json"
            json.dump(data, open(filename, "w"))

    def _send_query(self, query) -> Union[List, Dict]:
        cached = self._check_cache(query)
        if cached:
            return cached

        logger.debug(f"No cache for {query}")
        response = requests.get(f"{self._url}/{query}").json()

        if not self._cache:
            return response

        self._save_to_cache(query, response)
        return self._check_cache(query)

    def clear_cache(self, pattern: str = "*"):
        if self._redis_cache:
            for key in self._redis.keys(f"{self._prefix}{pattern}"):
                print(key)
                self._redis.delete(key)

        for file in glob.glob(f"cache/{pattern}.json"):
            os.remove(file)

    @property
    def seasons(self):
        return {
            2009: 9,
            2010: 16,
            2011: 37,
            2012: 44,
            2013: 45,
            2014: 48,
            2015: 49,
            2016: 50,
            2017: 51,
            2018: 52,
            2019: 53,
        }

    def _season_id(self, season_year: int):
        first_year, last_year = min(self.seasons.keys()), max(self.seasons.keys())
        if season_year < first_year or season_year > last_year:
            raise ValueError(
                f"No season ID for the year {season_year}, only {first_year}–{last_year} available"
            )
        return self.seasons[season_year]

    def player(self, player_id: int) -> Dict:
        return self._send_query(f"players/{player_id}")[0]

    def player_ratings(self, player_id: int) -> List:
        return self._send_query(f"players/{player_id}/rating")

    def player_rating(self, player_id: int, release_id: int = None) -> List:
        if not release_id:
            return self._send_query(f"players/{player_id}/rating/last")
        return self._send_query(f"players/{player_id}/rating/{release_id}")

    def player_teams(self, player_id: int) -> List:
        return self._send_query(f"players/{player_id}/teams")

    def player_all_tournaments(self, player_id: int) -> Dict:
        return self._send_query(f"players/{player_id}/tournaments")

    def player_tournaments(self, player_id: int, season: int = None) -> Dict:
        if not season:
            return self._send_query(f"players/{player_id}/tournaments/last")
        return self._send_query(
            f"players/{player_id}/tournaments/{self._season_id(season)}"
        )

    def team(self, team_id: int) -> Dict:
        return self._send_query(f"teams/{team_id}")[0]

    def team_ratings(self, team_id: int) -> Dict:
        return self._send_query(f"teams/{team_id}/rating")

    def team_rating(self, team_id: int, release_id: int = None) -> List:
        if not release_id:
            return self._send_query(f"teams/{team_id}/rating/last")
        return self._send_query(f"teams/{team_id}/rating/{release_id}")

    def team_rosters(self, team_id: int) -> Dict:
        return self._send_query(f"teams/{team_id}/recaps")

    def team_roster(self, team_id: int, season: int = None) -> List:
        if not season:
            return self._send_query(f"teams/{team_id}/recaps/last")
        return self._send_query(f"teams/{team_id}/recaps/{self._season_id(season)}")

    def team_all_tournaments(self, team_id: int) -> Dict:
        return self._send_query(f"teams/{team_id}/recaps")

    def team_tournaments(self, team_id: int, season: int = None) -> List:
        if not season:
            return self._send_query(f"teams/{team_id}/tournaments/last")
        return self._send_query(
            f"teams/{team_id}/tournaments/{self._season_id(season)}"
        )

    def tournament(self, tournament_id: int) -> Dict:
        return self._send_query(f"tournaments/{tournament_id}")[0]

    def tournament_results(self, tournament_id: int) -> List:
        return self._send_query(f"tournaments/{tournament_id}/list")

    def tournament_results_town(self, tournament_id: int, town_id: int) -> List:
        return self._send_query(f"tournaments/{tournament_id}/list/town/{town_id}")

    def tournament_results_region(self, tournament_id: int, region_id: int) -> List:
        return self._send_query(f"tournaments/{tournament_id}/list/town/{region_id}")

    def tournament_results_country(self, tournament_id: int, country_id: int) -> List:
        return self._send_query(f"tournaments/{tournament_id}/list/town/{country_id}")

    def tournament_rosters(self, tournament_id: int) -> List:
        return self._send_query(f"tournaments/{tournament_id}/recaps")

    def tournament_roster(self, tournament_id: int, team_id: int) -> List:
        return self._send_query(f"tournaments/{tournament_id}/recaps/{team_id}")

    def tournament_answers(self, tournament_id: int) -> List:
        return self._send_query(f"tournaments/{tournament_id}/controversials")

    def tournament_appeals(self, tournament_id: int) -> List:
        return self._send_query(f"tournaments/{tournament_id}/appeals")
