from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import httpx
import tempfile

from src.READMECreater.GithubFetcher import DownloadRepoFiles
from src.READMECreater.READMEGenerator import GenerateREADME
from src.TagCreater.Models import ExtractJson, ModelThreading
from src.Upload.Upload2DB import (
    GetVersion,
    SaveGitData,
    GetNextReadmeID,
    SavingCareerDB,
)
from src.Upload.Upload2Storage import UploadREADME
from src.Utils.GetJWT import GetDataFromToken, GetTokenFromHeader
from src.Utils.GetImage import GetImageInGithub
from src.Utils.DBClient import ReadGithubFromUserID, ReadREADMEDB

app = FastAPI(title="GitHub AI API")


class RepoRequest(BaseModel):
    git_url: str


# README 생성 API
@app.post("/api/career/readme")
async def GenerateReadme(request: RepoRequest):
    try:
        # README 쓰기
        repoURL = request.git_url
        repoFiles = DownloadRepoFiles(repoURL)
        readmeContent = GenerateREADME(repoURL, repoFiles)

        """ 이 부분은 token 연동 후 """
        # accessToken = GetTokenFromHeader(request)
        # userID = GetDataFromToken(accessToken, "user_id")
        userID = 312

        version = GetVersion(repoURL)
        readmeID = GetNextReadmeID()

        # README Storage & DB에 저장
        downloadURL = UploadREADME(readmeContent, userID, repoURL, version)
        SaveGitData(version, repoURL, readmeID, userID, downloadURL)

        return {
            "status": 200,
            "message": "요청에 성공하였습니다.",
            "data": f"/api/career/download?downloadURL={downloadURL}",  # 스토리지 내에 데이터를 user에게 streaming 하는 API Call
        }

    except Exception:
        return JSONResponse(
            status_code=400,
            content={"status": 400, "message": "README 생성 실패", "data": None},
        )


# README 다운로드 요청 처리 API
@app.get("/api/career/download")
async def DownloadFile(downloadURL: str):
    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(downloadURL)
            resp.raise_for_status()

            # 다운로드를 위한 임시 파일 생성
            with tempfile.NamedTemporaryFile(delete=False, suffix=".md") as tmp:
                tmp.write(resp.content)
                tmpPath = tmp.name

            return FileResponse(
                path=tmpPath,
                filename="README.md",
                media_type="application/octet-stream",
                headers={"Content-Disposition": 'attachment; filename="README.md"'},
            )

        except Exception:
            return JSONResponse(
                status_code=400,
                content={
                    "status": 400,
                    "message": "README 다운로드 실패",
                    "data": None,
                },
            )


# Tag 생성 API
@app.post("/api/career/tag")
async def GenerateTag(request: RepoRequest):
    try:
        githubURL = request.git_url
        response = ModelThreading(githubURL)
        tags = ExtractJson(response.text)

        """ 이 부분은 token 연동 후 """
        # accessToken = GetTokenFromHeader(request)
        # userID = GetDataFromToken(accessToken, "user_id")
        userID = 312
        imageURL = GetImageInGithub(githubURL)
        SavingCareerDB(tags, userID, githubURL, imageURL)

        return {
            "status": 200,
            "message": "요청에 성공하였습니다.",
            "data": tags,
        }

    except Exception:
        return JSONResponse(
            status_code=400,
            content={"status": 400, "message": "Tag 생성 실패", "data": None},
        )


# 유저가 올린 모든 github 정보 읽기
@app.get("/api/career/db/user")
async def ReadUserGithub(userID: int):
    try:
        data = ReadGithubFromUserID(userID)

        return {
            "status": 200,
            "message": "요청에 성공하였습니다.",
            "data": data,
        }
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"status": 400, "message": "DB read 실패", "data": None},
        )


# 유저가 올린 README 정보 읽기
@app.get("/api/career/db/readme")
async def ReadREADME(userID: int, gitURL: str):
    try:
        data = ReadREADMEDB(userID, gitURL)
        return {
            "status": 200,
            "message": "요청에 성공하였습니다.",
            "data": data,
        }
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"status": 400, "message": "DB read 실패", "data": None},
        )


# 헬스 체크
@app.get("/api/github-service/health-check")
async def HealthCheck():
    return {"status": 200, "message": "서버 상태 확인", "data": "Working"}
