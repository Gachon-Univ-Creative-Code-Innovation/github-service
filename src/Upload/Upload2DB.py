from src.Utils.DBClient import DBClientCall
from datetime import datetime


# README에서 version 정보 들고오기
def GetVersion(githubURL):
    supabase = DBClientCall()

    response = (
        supabase.table("README_Data")
        .select("version")
        .eq("github_url", githubURL)
        .order("version", desc=True)
        .limit(1)
        .execute()
    )

    # github_url에 대해서 이미 저장된 값이 있으면 version + 1
    if response.data:
        return response.data[0]["version"] + 1

    # 없으면 version = 1
    return 1


# 다음 readmeID를 디비에서 가져 옴
def GetNextReadmeID():
    supabase = DBClientCall()

    response = (
        supabase.table("README_Data")
        .select("readme_id")
        .order("readme_id", desc=True)
        .limit(1)
        .execute()
    )

    # readme_id을 자동으로 + 1해서 저장
    if response.data:
        return response.data[0]["readme_id"] + 1

    return 1


# DB에 해당 내용 저장
def SaveGitData(version, githubURL, readmeID, userID, downloadURL):
    supabase = DBClientCall()

    data = {
        "version": version,
        "github_url": githubURL,
        "readme_id": readmeID,
        "user_id": userID,
        "download_url": downloadURL,
    }
    supabase.table("README_Data").insert(data).execute()


# Career ID를 찾는 코드
def GetNextCareerID():
    supabase = DBClientCall()

    response = (
        supabase.table("Career_Meta_Data")
        .select("career_id")
        .order("career_id", desc=True)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]["career_id"] + 1

    return 1


# Career DB를 저장하는 코드
def SavingCareerDB(tagNames, userID, githubURL, imageURL):
    supabase = DBClientCall()

    # Career_Meta_Data 저장
    careerID = GetNextCareerID()
    timestamp = timestamp = datetime.utcnow().isoformat()
    data = {
        "career_id": careerID,
        "github_url": githubURL,
        "img_url": imageURL,
        "user_id": userID,
        "created_at": timestamp,
        "updated_at": timestamp,
    }
    supabase.table("Career_Meta_Data").insert(data).execute()

    for tagName in tagNames:
        # Career_Tag 저장
        data = {"c_tag":tagName, "career_id": careerID}
        supabase.table("Career_Tag").insert(data).execute()