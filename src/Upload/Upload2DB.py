import os
import psycopg2
from datetime import datetime
from dotenv import load_dotenv


# --- PostgreSQL 연결 함수 (환경변수 사용) ---
def get_pg_conn():
    envPath = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
    load_dotenv(dotenv_path=os.path.abspath(envPath))
    # 환경변수에서 직접 DB 접속 정보 읽기 (Kubernetes에서는 ConfigMap/Secret 등으로 주입)
    return psycopg2.connect(
        host=os.environ["PG_HOST"],
        dbname=os.environ["PG_DB"],
        user=os.environ["PG_USER"],
        password=os.environ["PG_PASSWORD"],
        port=int(os.environ.get("PG_PORT", 5432)),
    )


# README에서 version 정보 들고오기
# (Supabase → PostgreSQL 쿼리로 변경)
def GetVersion(githubURL):
    conn = get_pg_conn()  # PostgreSQL 연결
    cur = conn.cursor()
    cur.execute(
        'SELECT version FROM "README_Data" WHERE github_url=%s ORDER BY version DESC LIMIT 1',
        (githubURL,),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row[0] + 1
    return 1


# 다음 readmeID를 디비에서 가져 옴
# (Supabase → PostgreSQL 쿼리로 변경)
def GetNextReadmeID():
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute('SELECT readme_id FROM "README_Data" ORDER BY readme_id DESC LIMIT 1')
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row[0] + 1
    return 1


# DB에 해당 내용 저장
# (Supabase → PostgreSQL 쿼리로 변경)
def SaveGitData(version, githubURL, readmeID, userID, downloadURL, metaData):
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        INSERT INTO "README_Data" (version, github_url, readme_id, user_id, download_url, meta_data)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (version, githubURL, readmeID, userID, downloadURL, metaData),
    )
    conn.commit()
    cur.close()
    conn.close()


# Career ID를 찾는 코드
# (Supabase → PostgreSQL 쿼리로 변경)
def GetNextCareerID():
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute(
        'SELECT career_id FROM "Career_Meta_Data" ORDER BY career_id DESC LIMIT 1'
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row[0] + 1
    return 1


# Career DB를 저장하는 코드
# (Supabase → PostgreSQL 쿼리로 변경)
def SavingCareerDB(tagNames, userID, githubURL, imageURL):
    conn = get_pg_conn()
    cur = conn.cursor()
    careerID = GetNextCareerID()
    timestamp = datetime.utcnow().isoformat()
    # Career_Meta_Data 저장
    cur.execute(
        """
        INSERT INTO "Career_Meta_Data" (career_id, github_url, img_url, user_id, created_at, updated_at)
        VALUES (%s, %s, %s, %s, %s, %s)
        """,
        (careerID, githubURL, imageURL, userID, timestamp, timestamp),
    )
    # Career_Tag 저장
    for tagName in tagNames:
        cur.execute(
            'INSERT INTO "Career_Tag" (tag_name, career_id, user_id) VALUES (%s, %s, %s)',
            (tagName, careerID, userID),
        )
    conn.commit()
    cur.close()
    conn.close()
