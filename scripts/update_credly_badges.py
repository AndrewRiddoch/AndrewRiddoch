import os
import re
import sys
import requests

CREDLY_USERNAME = os.environ["CREDLY_USERNAME"]
README_PATH = "README.md"
START_MARKER = "<!-- CREDLY-BADGES:START -->"
END_MARKER = "<!-- CREDLY-BADGES:END -->"
BADGE_WIDTH = 120
username = os.getenv('CREDLY_USERNAME')

def fetch_badges(username: str) -> list[dict]:
    url = f"https://www.credly.com/users/{username}/badges.json"
    params = {"page": 1, "page_size": 100, "sort": "-issued_at_date"}
    all_badges = []

    while True:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
        data = payload.get("data", [])
        all_badges.extend(data)

        metadata = payload.get("metadata", {})
        if params["page"] >= metadata.get("total_pages", 1):
            break
        params["page"] += 1

    return all_badges


def build_markdown(badges: list[dict]) -> str:
    if not badges:
        return "_No public badges found._"

    items = []
    for b in badges:
        template = b.get("badge_template", {})
        name = template.get("name", "Credly badge")
        image_url = template.get("image_url", "")
        badge_id = b.get("id")
        url = f"https://www.credly.com/users/{username}/badges.json"
        link = f"https://www.credly.com/badges/{badge_id}" if badge_id else f"https://www.credly.com"
        items.append(f'<a href="{link}"><img src="{image_url}" alt="{name}" title="{name}" width="{BADGE_WIDTH}"></a>')

    return " ".join(items)


def update_readme(new_block: str) -> bool:
    with open(README_PATH, "r", encoding="utf-8") as f:
        content = f.read()

    pattern = re.compile(
        re.escape(START_MARKER) + r".*?" + re.escape(END_MARKER),
        re.DOTALL,
    )
    replacement = f"{START_MARKER}\n{new_block}\n{END_MARKER}"

    if not pattern.search(content):
        print("Markers not found in README.md", file=sys.stderr)
        sys.exit(1)

    updated = pattern.sub(replacement, content)
    changed = updated != content

    with open(README_PATH, "w", encoding="utf-8") as f:
        f.write(updated)

    return changed


def main():
    badges = fetch_badges(CREDLY_USERNAME)
    markdown_block = build_markdown(badges)
    changed = update_readme(markdown_block)

    # Expose to the workflow so it can decide whether to commit
    github_output = os.environ.get("GITHUB_OUTPUT")
    if github_output:
        with open(github_output, "a", encoding="utf-8") as f:
            f.write(f"changed={'true' if changed else 'false'}\n")


if __name__ == "__main__":
    main()
