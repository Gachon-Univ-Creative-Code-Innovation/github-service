import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.READMECreater.GithubFetcher import DownloadRepoFiles
from src.READMECreater.READMEGenerator import GenerateREADME
from src.Upload.Upload2DB import GetVersion, SaveGitData, GetNextReadmeID
from src.Upload.Upload2Storage import UploadREADME


repoURL = input("GitHub URL 입력: ")
repoFiles = DownloadRepoFiles(repoURL)
readmeContent = GenerateREADME(repoURL, repoFiles)
userID = 312

version = GetVersion(repoURL)
readmeID = GetNextReadmeID()

# README Storage & DB에 저장
downloadURL = UploadREADME(readmeContent, userID, repoURL, version)
SaveGitData(version, repoURL, readmeID, userID, downloadURL)

print(f"/api/career/download?downloadURL={downloadURL}")
