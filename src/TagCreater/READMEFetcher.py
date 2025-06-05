import requests
from urllib.parse import urlparse
import base64


# URL에서 owner와 repo 이름을 추출하는 함수
def RepoInfo(repoURL):
    url = urlparse(repoURL)
    path = url.path.strip("/").split("/")
    return (path[0], path[1]) if len(path) >= 2 else (None, None)


# GitHub API를 사용하여 README.md 파일을 가져오는 함수
def GetREADME(repoURL, gitToken=None):
    owner, repo = RepoInfo(repoURL)
    if not owner or not repo:
        print("Invalid GitHub URL.")
        return None

    apiURL = f"https://api.github.com/repos/{owner}/{repo}/readme"
    headers = {"Accept": "application/vnd.github.v3+json"}
    if gitToken:
        headers = {"Authorization": f"Bearer {gitToken}"} if gitToken else {}

    response = requests.get(apiURL, headers=headers)
    if response.status_code == 200:
        return base64.b64decode(response.json()["content"]).decode("utf-8")

    return None
