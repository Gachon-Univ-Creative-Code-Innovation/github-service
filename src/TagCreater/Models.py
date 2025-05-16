import json
import re
import os
from dotenv import load_dotenv
import threading
import json
import google.generativeai as genai
from groq import Groq

from src.TagCreater.READMEFetcher import GetREADME
from src.TagCreater.TagMerger import MergeCleanTags


results = {}


# <think>와 </think> 사이의 내용을 포함하여 모두 제거
def RemoveThink(text):
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return cleaned


# 응답에서 tags 키 아래의 JSON 목록을 추출하는 함수
def ExtractJson(text):
    match = re.search(r'({\s*"tags"\s*:\s*\[.*?\]\s*})', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))["tags"]
        except json.JSONDecodeError:
            print("JSON parsing failed.")
            return []
    raise ValueError("Valid JSON format not found.")


# LLM 호출 함수
def CallLLM(modelName, readmeContent, client):
    if not readmeContent:
        print(f"README.md not found. ({modelName})")
        return

    try:
        chatCompletion = client.chat.completions.create(
            messages=[
                {
                    "role": "system",
                    "content": (
                        "Extract key technologies in JSON format with this format only:\n"
                        '{ "tags": ["tech1", "tech2", ...] }\n'
                        "Return only JSON. No explanation."
                    ),
                },
                {"role": "user", "content": readmeContent[:1000]},  # 1000자 제한
            ],
            model=modelName,
            temperature=0,
        )

        content = chatCompletion.choices[0].message.content
        print(f"\n[{modelName}] Raw Output:\n{content}\n{'-'*50}")

        results[modelName] = ExtractJson(RemoveThink(content))

    except Exception as e:
        print(f"Exception in {modelName}: {e}")


# Gemini 호출 함수
def CallGemini(readme_content, gemini_model):
    if not readme_content:
        print("README.md not found. (Gemini)")
        return

    try:
        prompt = (
            "Extract key technologies in JSON format like:\n"
            '{ "tags": ["tech1", "tech2", ...] }\n'
            "Return only JSON. No explanation."
        )
        response = gemini_model.generate_content(
            f"{prompt}\n\nUser: {readme_content[:1000]}"  # 1000자 제한
        )

        print(f"\n[Gemini] Raw Output:\n{response.text}\n{'-'*50}")

        results["gemini"] = ExtractJson(RemoveThink(response.text))

    except Exception as e:
        print(f"Gemini exception: {e}")


# Model 실행 함수
def ModelThreading(url):
    envPath = os.path.join(os.path.dirname(__file__), "..", ".env")
    load_dotenv(dotenv_path=os.path.abspath(envPath))
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
    GITHUB_TOKEN = os.getenv("GH_API_TOKEN")

    # Input
    readmeContent = GetREADME(url, GITHUB_TOKEN)

    # 모델 부르기
    client = Groq(api_key=GROQ_API_KEY)
    genai.configure(api_key=GOOGLE_API_KEY)
    gemini = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-01-21")

    # LLM Thread에서 호출
    models = ["gemma2-9b-it", "llama-3.3-70b-versatile"]
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

    refiner = genai.GenerativeModel("gemini-2.0-flash-thinking-exp-01-21")
    response = refiner.generate_content(
        f'{json.dumps(resultJson, ensure_ascii=False)} Extract only key technologies in JSON format as "tags": []'
    )

    return response
