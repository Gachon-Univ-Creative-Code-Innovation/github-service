import os
from dotenv import load_dotenv
from supabase import create_client, Client


# DB에 접근하는 Key 부르는 함수
def DBClientCall():
    envPath = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    load_dotenv(dotenv_path=os.path.abspath(envPath))

    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")

    # DB 접근 Client 생성
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

    return supabase


# DB Bucket 이름 불러오는 함수
def BucketCall():
    SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")

    return SUPABASE_BUCKET


# 유저 ID로 Tag 생성한 모든 정보 가져오기
def ReadGithubFromUserID(userID):
    supabase: Client = DBClientCall()

    # SQL 작성
    sql = f"""
    SELECT * FROM "Career_Tag"
    INNER JOIN "Career_Meta_Data" ON "Career_Tag".career_id = "Career_Meta_Data".career_id
    WHERE "Career_Meta_Data".user_id = {int(userID)}
    """

    # SQL 실행
    response = supabase.rpc("execute_sql", {"query": sql}).execute()

    return [item["result"] for item in response.data]


# 유저 ID와 github url이 같은 Github의 Image 가져오기
def ReadImageFromUserID(userID, githubURL):
    supabase: Client = DBClientCall()

    # userID와 githubURL의 타입 확인
    print(f"userID: {userID}, githubURL: {githubURL}")

    sql = f"""
    SELECT img_url FROM "Career_Meta_Data"
    WHERE "Career_Meta_Data".user_id={int(userID)} 
    and "Career_Meta_Data".github_url='{githubURL}'
    ORDER BY "Career_Meta_Data".career_id DESC
    LIMIT 1
    """

    response = supabase.rpc("execute_sql", {"query": sql}).execute()

    if response.data:
        return response.data[0]["result"]["img_url"]
    else:
        return None  # 데이터가 없으면 None 반환


# 유저ID와 github url이 같은 모든 version의 readme 읽어오기
def ReadREADMEDB(userID, githubURL):
    supabase: Client = DBClientCall()

    sql = f"""
    SELECT * FROM "README_Data"
    WHERE "README_Data".user_id={int(userID)} 
    and "README_Data".github_url='{githubURL}'
    ORDER BY "README_Data".readme_id DESC
    """

    # SQL 실행
    response = supabase.rpc("execute_sql", {"query": sql}).execute()

    return [item["result"] for item in response.data]
