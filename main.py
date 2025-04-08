from fastapi import FastAPI
from fastapi.responses import JSONResponse, FileResponse
from pydantic import BaseModel
from src.READMECreater.GithubFetcher import DownloadRepoFiles
from src.READMECreater.READMEGenerator import GenerateREADME
from io import StringIO

app = FastAPI(title="GitHub README Generator API")


class RepoRequest(BaseModel):
    git_url: str


# README 생성 API
@app.post("/api/career/readme")
async def generate_readme(request: RepoRequest):
    try:
        repoURL = request.git_url
        repoFiles = DownloadRepoFiles(repoURL)
        readmeContent = GenerateREADME(repoURL, repoFiles)
        
        filePath = "/tmp/README.md"
        with open(filePath, "w", encoding="utf-8") as f:
            f.write(readmeContent)
        
        '''
        return {
            "status": "200",
            "message": "요청에 성공하였습니다.",
            "data": f"/files/README.md"
        }
        '''

        return FileResponse(
            filePath, 
            filename="README.md", 
            headers={"Content-Disposition": "attachment; filename=README.md"}
        )
        
    except Exception:
        return JSONResponse(
            status_code=400,
            content={"status": 400, "message": "README 생성 실패", "data": None},
        )
