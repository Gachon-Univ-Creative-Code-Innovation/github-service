import os
from dotenv import load_dotenv
import threading
import json
import google.generativeai as genai
from groq import Groq
from fastapi import FastAPI, Response
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
import httpx
import tempfile


from src.READMECreater.GithubFetcher import DownloadRepoFiles
from src.READMECreater.READMEGenerator import GenerateREADME
from src.TagCreater.READMEFetcher import GetREADME
from src.TagCreater.Models import CallLLM, CallGemini, ExtractJson, results
from src.TagCreater.TagMerger import MergeCleanTags
from src.Upload.Upload2DB import GetVersion, SaveMetadata, GetNextReadmeID
from src.Upload.Upload2Storage import UploadREADME
from src.Utils.GetJWT import GetDataFromToken, GetTokenFromHeader

app = FastAPI(title="GitHub README Generator API")


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
        SaveMetadata(version, repoURL, readmeID, userID, downloadURL)

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
        # API Keys
        envPath = os.path.join(os.path.dirname(__file__), "..", ".env")
        load_dotenv(dotenv_path=os.path.abspath(envPath))
        GROQ_API_KEY = os.getenv("GROQ_API_KEY")
        GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
        GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

        # Input
        url = request.git_url
        readmeContent = GetREADME(url, GITHUB_TOKEN)

        # 모델 부르기
        client = Groq(api_key=GROQ_API_KEY)
        genai.configure(api_key=GOOGLE_API_KEY)
        gemini = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-01-21")

        # LLM Thread에서 호출
        models = ["qwen-2.5-coder-32b", "llama-3.3-70b-versatile"]
        threads = [
            threading.Thread(target=CallLLM, args=(model, readmeContent, client))
            for model in models
        ]
        for thread in threads:
            thread.start()

        geminiThread = threading.Thread(target=CallGemini, args=(readmeContent, gemini))
        threads.append(geminiThread)
        geminiThread.start()

        for thread in threads:
            thread.join()

        # Output
        for model, tags in results.items():
            print(f"Model: {model}")
            print(tags)
            print("-" * 50)

        FinalTags = MergeCleanTags(*[results[m] for m in results])
        resultJson = {"tags": FinalTags}

        refiner = genai.GenerativeModel("learnlm-1.5-pro-experimental")
        response = refiner.generate_content(
            f'{json.dumps(resultJson, ensure_ascii=False)} Extract only key technologies in JSON format as "tags": []'
        )

        return {
            "status": 200,
            "message": "요청에 성공하였습니다.",
            "data": ExtractJson(response.text),
        }

    except Exception:
        return JSONResponse(
            status_code=400,
            content={"status": 400, "message": "Tag 생성 실패", "data": None},
        )


# 헬스 체크
@app.get("/api/github-service/health-check")
async def HealthCheck():
    return {"status": 200, "message": "서버 상태 확인", "data": "Working"}
