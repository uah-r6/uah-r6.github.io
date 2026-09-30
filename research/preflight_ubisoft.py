"""Find official replay links and game metadata without downloading ZIPs.

Usage: python research/preflight_ubisoft.py FIRST_ID LAST_ID
Fetched match pages are cached under ignored data/research/diagnostics/.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path
import sys
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / "data/research/diagnostics/ubisoft-pages"
URL = "https://www.ubisoft.com/en-us/esports/rainbow-six/siege/match/{}"


def page(match_id: int) -> str | None:
    path = CACHE / f"{match_id}.html"
    if path.exists() and path.stat().st_size:
        return path.read_text(encoding="utf-8")
    request = Request(URL.format(match_id), headers={"User-Agent": "Mozilla/5.0"})
    try:
        with urlopen(request, timeout=20) as response:
            content = response.read().decode("utf-8")
    except (HTTPError, URLError, TimeoutError):
        return None
    CACHE.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return content


def details(match_id: int) -> dict | None:
    content = page(match_id)
    if not content:
        return None
    marker = content.find('id="__NEXT_DATA__"')
    if marker < 0:
        return None
    start = content.find(">", marker) + 1
    end = content.find("</script>", start)
    if start == 0 or end < 0:
        return None
    try:
        data = json.loads(content[start:end])["props"]["pageProps"]["pageData"]
        match = data["match"]
        names = {team["id"]: team["name"] for team in data["teams"]}
        team_names = [names.get(team["id"], str(team["id"])) for team in match["teams"]]
        return {"id": match_id, "date": match["date"], "teams": team_names,
                "maps": [(game.get("map") or {}).get("name") for game in match["games"]],
                "replay_url": match.get("replayLink")}
    except (KeyError, TypeError, ValueError):
        return None


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("Usage: preflight_ubisoft.py FIRST_ID LAST_ID")
    first, last = map(int, sys.argv[1:])
    if last < first or last - first > 200:
        raise ValueError("Choose an inclusive ascending range of at most 201 IDs")
    with ThreadPoolExecutor(max_workers=6) as pool:
        for row in pool.map(details, range(first, last + 1)):
            if row and row["replay_url"]:
                print(json.dumps(row, ensure_ascii=True), flush=True)


if __name__ == "__main__":
    main()
