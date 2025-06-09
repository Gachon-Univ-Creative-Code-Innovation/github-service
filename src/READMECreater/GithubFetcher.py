import os
import re
import requests
from dotenv import load_dotenv

# Github API Token을 사용하여 요청 헤더 설정
envPath = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(envPath))

GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
HEADERS = {"Authorization": f"token {GITHUB_TOKEN}"} if GITHUB_TOKEN else {}

# 지원하는 프로그래밍 언어별 확장자
LANGUAGE_EXTENSIONS = {
    "java": ".java",
    "c": ".c",
    "go": ".go",
    "typescript": ".ts",
    "javascript": ".js",
    "ruby": ".rb",
    "csharp": ".cs",
    "cpp": [".cpp", ".hpp", ".cc", ".cxx"],
    "php": ".php",
    "python": ".py",
}


# 파일 확장자가 지원하는 언어 목록에 포함되는지 확인하는 함수
def IsValidExtension(fileName):
    return any(
        (
            fileName.endswith(ext)
            if isinstance(ext, str)
            else any(fileName.endswith(e) for e in ext)
        )
        for ext in LANGUAGE_EXTENSIONS.values()
    )


# GitHub 저장소의 모든 코드 파일을 재귀적으로 가져오는 함수
def FetchFiles(url):
    print(f"[FetchFiles] 요청 URL: {url}")  # 디버깅용
    response = requests.get(url, headers=HEADERS)
    print(f"[FetchFiles] 응답 status: {response.status_code}")  # 디버깅용
    if response.status_code != 200:
        print(f"[FetchFiles] 오류 응답 내용: {response.text}")  # 디버깅용
        raise Exception(f"Failed to fetch repository contents: {response.text}")

    files = []
    for item in response.json():
        print(
            f"[FetchFiles] item: {item.get('name')} / type: {item.get('type')}"
        )  # 디버깅용
        if item["type"] == "file" and IsValidExtension(item["name"]):
            print(f"[FetchFiles] 파일 다운로드: {item['download_url']}")  # 디버깅용
            file_content = requests.get(item["download_url"], headers=HEADERS).text
            files.append((item["name"], file_content))
        elif item["type"] == "dir":
            print(f"[FetchFiles] 디렉토리 진입: {item['url']}")  # 디버깅용
            files.extend(FetchFiles(item["url"]))
    return files


# GitHub 저장소의 모든 코드 파일을 가져오는 함수
def DownloadRepoFiles(repoURL):
    print(f"[DownloadRepoFiles] 입력 repoURL: {repoURL}")  # 디버깅용
    repoPath = re.sub(r"https://github.com/|.git$", "", repoURL.strip("/"))
    print(f"[DownloadRepoFiles] 변환된 repoPath: {repoPath}")  # 디버깅용
    apiURL = f"https://api.github.com/repos/{repoPath}/contents/"
    print(f"[DownloadRepoFiles] 호출할 apiURL: {apiURL}")  # 디버깅용
    return FetchFiles(apiURL)


# 지원하는 프로그래밍 언어별 확장자를 반환하는 함수
def GetLanguageExtensions():
    return LANGUAGE_EXTENSIONS
