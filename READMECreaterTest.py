from src.READMECreater.GithubFetcher import DownloadRepoFiles
from src.READMECreater.READMEGenerator import GenerateREADME


repo_url = input("GitHub URL 입력: ")
files = DownloadRepoFiles(repo_url)
readme = GenerateREADME(repo_url, files)

with open("README.md", "w") as f:
    f.write(readme)

print("README.md 생성 완료!")
