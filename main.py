import os
from dotenv import load_dotenv
import threading
import json
import google.generativeai as genai
from groq import Groq
from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel


from src.READMECreater.GithubFetcher import DownloadRepoFiles
from src.READMECreater.READMEGenerator import GenerateREADME
from src.TagCreater.READMEFetcher import GetREADME
from src.TagCreater.Models import CallLLM, CallGemini, ExtractJson, results
from src.TagCreater.TagMerger import MergeCleanTags


app = FastAPI(title="GitHub README Generator API")


class RepoRequest(BaseModel):
    git_url: str


# README 생성 API
@app.post("/api/career/readme")
async def GenerateReadme(request: RepoRequest):
    try:
        repoURL = request.git_url
        repoFiles = DownloadRepoFiles(repoURL)
        readmeContent = GenerateREADME(repoURL, repoFiles)

        filePath = "/tmp/README.md"
        with open(filePath, "w", encoding="utf-8") as f:
            f.write(readmeContent)

        """
        return {
            "status": "200",
            "message": "요청에 성공하였습니다.",
            "data": f"/files/README.md"
        }
        """

        return FileResponse(
            filePath,
            filename="README.md",
            headers={"Content-Disposition": "attachment; filename=README.md"},
        )

    except Exception:
        return JSONResponse(
            status_code=400,
            content={"status": 400, "message": "README 생성 실패", "data": None},
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
            "status": "200",
            "message": "요청에 성공하였습니다.",
            "data": ExtractJson(response.text),
        }

    except Exception:
        return JSONResponse(
            status_code=400,
            content={"status": 400, "message": "Tag 생성 실패", "data": None},
        )
