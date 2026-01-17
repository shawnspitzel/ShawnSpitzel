from datetime import datetime
import os
import requests
from dotenv import load_dotenv

load_dotenv()

graphql_url = "https://api.github.com/graphql"

STATS_QUERY = f"""
query userInfo($login: String!) {{
  user(login: $login) {{
    name
    login
    commits: contributionsCollection(from: "{datetime.now().year}-01-01T00:00:00Z") {{
      totalCommitContributions
    }}
    reviews: contributionsCollection {{
      totalPullRequestReviewContributions
    }}
    repositoriesContributedTo(first: 1, contributionTypes: [COMMIT, ISSUE, PULL_REQUEST, REPOSITORY]) {{
      totalCount
    }}
    pullRequests(first: 1) {{
      totalCount
    }}
    mergedPullRequests: pullRequests(states: MERGED) {{
      totalCount
    }}
    openIssues: issues(states: OPEN) {{
      totalCount
    }}
    closedIssues: issues(states: CLOSED) {{
      totalCount
    }}
    followers {{
      totalCount
    }}
    repositoryDiscussions {{
      totalCount
    }}
    repositoryDiscussionComments(onlyAnswers: true) {{
      totalCount
    }}
    repositories(first: 100, ownerAffiliations: OWNER) {{
      totalCount
      nodes {{
        name
        stargazers {{
          totalCount
        }}
      }}
    }}
  }}
}}
"""

LANGUAGES_QUERY = """
query userInfo($login: String!) {
  user(login: $login) {
    repositories(ownerAffiliations: OWNER, isFork: false, first: 100) {
      nodes {
        name
        languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
          edges {
            size
            node {
              color
              name
            }
          }
        }
      }
    }
  }
}
"""


def generate_readme(username: str, token: str, path: str = "README-Generated.md"):
    stats = get_stats(username, token)
    languages = get_languages(username, token)

    with open(path, "w", encoding="utf-8") as readme:
        readme.write(f"_Last updated: {datetime.now()}_\n")

        readme.write("## 📊 Stats\n")
        readme.write("```\n")
        readme.write(f"Total Stars:    {stats['stars']}\n")
        readme.write(f"Total Commits:  {stats['commits']}\n")
        readme.write(f"Total PRs:      {stats['prs']}\n")
        readme.write(f"Contributed to: {stats['contributed_to']}\n")
        readme.write("```\n")

        readme.write("\n")

        readme.write("## 💻 Top Languages\n")
        readme.write("```\n")
        total_size = sum(size for _, size in languages.items())
        for lang, size in list(languages.items())[:10]:
            percent = (size / total_size) * 100 if total_size > 0 else 0
            bar = percent_bar(percent)
            readme.write(f"{lang:<12} {bar} {percent:.2f}%\n")
        readme.write("```\n")


def get_stats(username: str, token: str):
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json",
    }

    payload = {"query": STATS_QUERY, "variables": {"login": username}}

    response = requests.post(graphql_url, json=payload, headers=headers)
    response.raise_for_status()

    data = response.json()["data"]["user"]

    stats = {}

    for repository in data["repositories"]["nodes"]:
        stats["stars"] = stats.get("stars", 0) + repository["stargazers"]["totalCount"]

    stats["commits"] = data["commits"]["totalCommitContributions"]
    stats["prs"] = data["pullRequests"]["totalCount"]
    stats["contributed_to"] = data["repositoriesContributedTo"]["totalCount"]

    return stats


def get_languages(username: str, token: str):
    headers = {
        "Authorization": f"token {token}",
        "Content-Type": "application/json",
    }

    payload = {"query": LANGUAGES_QUERY, "variables": {"login": username}}

    response = requests.post(graphql_url, json=payload, headers=headers)
    response.raise_for_status()

    data = response.json()["data"]["user"]["repositories"]["nodes"]

    languages = {}
    for repo in data:
        edges = repo["languages"]["edges"]
        if not edges:
            continue

        for edge in edges:
            lang_name = edge["node"]["name"]
            lang_size = edge["size"]

            languages[lang_name] = languages.get(lang_name, 0) + lang_size

    sorted_languages = dict(
        sorted(
            languages.items(),
            key=lambda pair: pair[1],
            reverse=True,
        )
    )

    return sorted_languages


def percent_bar(percent: float, width: int = 20):
    percent = max(0, min(100, percent))
    filled = round((percent / 100) * width)
    empty = width - filled

    return f"[{'█' * filled}{'░' * empty}]"


if __name__ == "__main__":
    username = "shawnspitzel"
    token = os.getenv("GITHUB_TOKEN", "")

    generate_readme(username, token)