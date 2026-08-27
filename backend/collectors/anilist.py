"""AniList collector (GraphQL API, public, no key)."""
from __future__ import annotations

from .web import http_post_json

URL = "https://graphql.anilist.co"

QUERY = """
query ($id: Int) {
  Media(idMal: $id, type: ANIME) {
    id idMal
    title { romaji english native userPreferred }
    synonyms format type status description siteUrl updatedAt hashtag
    startDate { year month day } endDate { year month day }
    season seasonYear episodes duration countryOfOrigin
    isAdult isLicensed source averageScore meanScore popularity favourites trending
    coverImage { extraLarge large medium color }
    bannerImage genres tags {
      id name description category rank isGeneralSpoiler isMediaSpoiler isAdult
    }
    trailer { id site thumbnail }
    nextAiringEpisode {
      id airingAt timeUntilAiring episode mediaId
    }
    rankings { id rank type format year season allTime context }
    studios { edges { isMain node { id name siteUrl isAnimationStudio } } }
    staff (sort: [RELEVANCE, ID], perPage: 60) {
      edges { role node { id name { full native } language primaryOccupations
        image { large medium } } }
    }
    characters (sort: [RELEVANCE, ROLE], perPage: 60) {
      edges { role node { id name { full native } image { large } description }
        voiceActors (language: JAPANESE) { id name { full native } image { large } } }
    }
    relations { edges { relationType node { id type title { romaji english native } format coverImage { medium } status } } }
    recommendations (page: 1, perPage: 30, sort: RATING) {
      nodes { rating mediaRecommendation { id title { romaji english } format coverImage { medium } bannerImage } }
    }
    externalLinks { id site url type language color icon }
    streamingEpisodes { title thumbnail url site }
    stats {
      scoreDistribution { score amount }
      statusDistribution { status amount }
    }
    reviews (page: 1, perPage: 10, sort: RATING) {
      nodes { id summary rating user { name avatar { medium } } score createdAt }
    }
  }
}
"""


def collect(entry: dict, progress=None) -> dict:
    if progress:
        progress(f"AniList #{entry['anilist']} {entry['en']}")
    payload = {"query": QUERY, "variables": {"id": entry["mal"]}}
    data = http_post_json(URL, payload, retries=4)
    media = (data.get("data") or {}).get("Media")
    if not media:
        raise RuntimeError(f"AniList: no data for idMal {entry['mal']}")
    # prettify: move every top-level field we know we fetched into one dict
    result = {"source": "anilist", "id": media.get("id"), "fetched_at_utc": None}
    result.update(media)
    result["_query_fields"] = sorted(media.keys())
    return result