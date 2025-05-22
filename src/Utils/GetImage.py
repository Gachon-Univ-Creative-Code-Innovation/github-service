import os
import re
import requests
from dotenv import load_dotenv

from src.TagCreater.READMEFetcher import GetREADME, RepoInfo

# Github API Token을 사용하여 요청 헤더 설정
envPath = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(envPath))


# 상수 정의
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}
IMAGE_EXTENSIONS = [".jpg", ".jpeg", ".png", ".gif", ".webp", ".bmp", ".svg"]


# 상대 이미지 URL 수정
def ResolveImageURL(imgURL, repoURL):
    if imgURL.startswith("http"):
        return imgURL

    # 상대 경로 처리
    repoPath = re.sub(r"https://github.com/|.git$", "", repoURL.strip("/"))
    imgURL = imgURL.lstrip("./")

    return f"https://raw.githubusercontent.com/{repoPath}/main/{imgURL}"


# 이미지 확장자 확인 함수
def IsImageFile(fileName):
    return any(fileName.lower().endswith(ext) for ext in IMAGE_EXTENSIONS)


# GitHub 저장소에서 이미지 파일 탐색
def FetchImageFiles(url):
    response = requests.get(url, headers=HEADERS)
    if response.status_code != 200:
        raise Exception(f"Failed to fetch repository contents: {response.json()}")

    images = []
    for item in response.json():
        if item["type"] == "file" and IsImageFile(item["name"]):
            images.append(
                {
                    "name": item["name"],
                    "path": item["path"],
                    "download_url": item["download_url"],
                }
            )
        elif item["type"] == "dir":
            images.extend(FetchImageFiles(item["url"]))  # 재귀적으로 탐색
    return images


# branch 이름이 main과 다를 때 값 가져오기
def GetDefaultBranch(repoPath):
    url = f"https://api.github.com/repos/{repoPath}"
    res = requests.get(url, headers=HEADERS)

    if res.status_code == 200:
        return res.json().get("default_branch", "main")
    raise Exception(
        f"Repository not found or access denied. Status: {res.status_code}, msg: {res.json().get('message')}"
    )


# 레포 안에 image 찾기
def FindImagesInRepo(repoURL):
    repoPath = RepoInfo(repoURL)
    defaultBranch = GetDefaultBranch(repoPath)
    apiURL = f"https://api.github.com/repos/{repoPath}/contents/?ref={defaultBranch}"
    return FetchImageFiles(apiURL)


# 이미지 점수화
def GetImageScore(path):
    name = os.path.basename(path).lower()
    score = 0

    # 파일 이름에 2가지가 있을 경우
    if "screenshot" in name or "demo" in name:
        score += 10
    # 파일 이름에 특정 키워드가 있으면
    if any(keyword in name for keyword in ["logo", "cover", "main", "banner"]):
        score += 6
    # 파일 경로가 "assets"나 "docs", "test" 폴더
    if path.startswith("assets") or path.startswith("docs") or path.startswith("test"):
        score += 6
    # 경로가 단순할 때
    if path.count("/") <= 2:
        score += 4

    return score


# 점수화해서 가장 높은 이미지 선택
def ChooseImage(imgURLs):
    scored = [(img, GetImageScore(img["path"])) for img in imgURLs]
    scored.sort(key=lambda x: x[1], reverse=True)

    return scored[0][0] if scored else None


# 사이트가 404인지 확인
def Is404(url):
    try:
        response = requests.head(url, allow_redirects=True)
        return response.status_code != 404
    except requests.RequestException as e:
        return False


# github에 속한 이미지 가져오기
def GetImageInGithub(repoURL):
    readmeContent = GetREADME(repoURL, GITHUB_TOKEN)
    # README에 이미지 있으면 가져옴
    if readmeContent:
        match = re.search(r'<img\s+src="([^"]+)"', readmeContent)
    else:
        match = None

    if match:
        imgURL = match.group(1)
        imgURL = ResolveImageURL(imgURL, repoURL)
        if Is404(imgURL):
            return imgURL

    # README에 없으면 폴더 확인
    imgURLs = FindImagesInRepo(repoURL)
    chosen = ChooseImage(imgURLs)
    imgURL = chosen["download_url"] if chosen else None
    return imgURL
