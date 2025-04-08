import json
import re
import google.generativeai as genai
from groq import Groq

results = {}


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

        results[modelName] = ExtractJson(content)

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

        results["gemini"] = ExtractJson(response.text)

    except Exception as e:
        print(f"Gemini exception: {e}")
