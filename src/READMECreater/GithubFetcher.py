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
    response = requests.get(url, headers=HEADERS)
    # 요청 실패 시 예외 처리
    if response.status_code != 200:
        raise Exception(f"Failed to fetch repository contents: {response.json()}")

    # JSON 응답에서 파일 및 디렉토리 정보 추출
    files = []
    for item in response.json():
        if item["type"] == "file" and IsValidExtension(item["name"]):
            file_content = requests.get(item["download_url"], headers=HEADERS).text
            files.append((item["name"], file_content))
        elif item["type"] == "dir":
            files.extend(FetchFiles(item["url"]))
    return files


# GitHub 저장소의 모든 코드 파일을 가져오는 함수
def DownloadRepoFiles(repoURL):
    repoPath = re.sub(r"https://github.com/|.git$", "", repoURL.strip("/"))
    apiURL = f"https://api.github.com/repos/{repoPath}/contents/"
    return FetchFiles(apiURL)


# 지원하는 프로그래밍 언어별 확장자를 반환하는 함수
def GetLanguageExtensions():
    return LANGUAGE_EXTENSIONS
