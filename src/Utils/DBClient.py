import os
import psycopg2
from dotenv import load_dotenv
from supabase import create_client, Client


# PostgreSQL 연결 함수 (환경변수 사용)
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
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute(
        'SELECT github_url, version, download_url, meta_data FROM "README_Data" WHERE user_id = %s',
        (int(userID),),
    )
    rows = cur.fetchall()
    cur.close()
    conn.close()
    # 결과를 dict로 변환
    return [
        {
            "github_url": row[0],
            "version": row[1],
            "download_url": row[2],
            "meta_data": row[3],
        }
        for row in rows
    ]


# 유저 ID와 github url이 같은 Github의 Image 가져오기
def ReadImageFromUserID(userID, githubURL):
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT img_url FROM \"Career_Meta_Data\"
        WHERE user_id = %s AND github_url = %s
        ORDER BY career_id DESC
        LIMIT 1
        """,
        (int(userID), githubURL),
    )
    row = cur.fetchone()
    cur.close()
    conn.close()
    if row:
        return row[0]
    else:
        return None  # 데이터가 없으면 None 반환


# 유저ID와 github url이 같은 모든 version의 readme 읽어오기
def ReadREADMEDB(userID, githubURL):
    conn = get_pg_conn()
    cur = conn.cursor()
    cur.execute(
        """
        SELECT * FROM \"README_Data\"
        WHERE user_id = %s AND github_url = %s
        ORDER BY readme_id DESC
        """,
        (int(userID), githubURL),
    )
    rows = cur.fetchall()
    # 컬럼명 가져오기
    colnames = [desc[0] for desc in cur.description]
    cur.close()
    conn.close()
    # 결과를 dict로 변환
    return [dict(zip(colnames, row)) for row in rows]
