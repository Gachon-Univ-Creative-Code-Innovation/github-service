from urllib.parse import urlparse
from src.Utils.DBClient import DBClientCall, BucketCall
import tempfile


# github 주소에서 ower와 repo_name 추출
def ExtractOwnerRepo(githubURL):
    parsed = urlparse(githubURL)
    parts = parsed.path.strip("/").split("/")

    if len(parts) >= 2:
        return parts[0], parts[1]
    else:
        return parts[0]


# README 파일 올리기
def UploadREADME(content, userID, githubURL, version):
    # 환경 변수 부르기
    bucket = BucketCall()
    supabase = DBClientCall()

    # 데이터 저장하기 위한 정보 추출
    owner, repo = ExtractOwnerRepo(githubURL)
    fileName = f"README_{owner}_{repo}/userID{userID}_v{version}.md"

    # README를 DB에 저장하기 위해서 임시 저장
    with tempfile.NamedTemporaryFile(
        delete=False, mode="w", encoding="utf-8", suffix=".md"
    ) as tmp:
        tmp.write(content)
        tmpPath = tmp.name

    # DB에 저장 요청
    response = supabase.storage.from_(bucket).upload(
        fileName, tmpPath, {"content-type": "text/markdown", "x-upsert": "true"}
    )

    # 오류 처리
    if hasattr(response, "error") and response.error:
        print("Storage Save Error")
        return None

    # Bucket 접근 URL return
    return supabase.storage.from_(bucket).get_public_url(fileName)
