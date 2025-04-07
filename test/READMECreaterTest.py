import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.READMECreater.GithubFetcher import DownloadRepoFiles
from src.READMECreater.READMEGenerator import GenerateREADME


repoURL = input("GitHub URL 입력: ")
files = DownloadRepoFiles(repoURL)
readme = GenerateREADME(repoURL, files)

with open("README.md", "w") as f:
    f.write(readme)

print("README.md 생성 완료!")
