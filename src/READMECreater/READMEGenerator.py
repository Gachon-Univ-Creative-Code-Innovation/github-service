import os
import re
import requests
from dotenv import load_dotenv
from src.READMECreater.CodeAnalyzer import SummarizeKeywords
from src.READMECreater.CodeAnalyzer import AnalyzeRepository

# .env 경로 로딩
envPath = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(envPath))

VLLM_SERVER_URL = os.getenv("VLLM_SERVER_URL")

def RemoveThink(text):
    cleaned = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    return cleaned.strip()

def GeneratePrompt(repoName, imports, functions, comments):
    imports = [imp for imp in imports if imp]
    functions = [func for func in functions if func]
    comments = [cmt for cmt in comments if cmt]

    imports = list(set(imports))
    functions = SummarizeKeywords(functions)
    comments = sorted(comments, key=len, reverse=True)[:5]

    # system role에서 설명할 수 있게 user 프롬프트는 핵심 데이터만 전달
    content = f"""
Repository Name: {repoName}

## Used Libraries
{", ".join(imports) if imports else "No external libraries found."}

## Function Overview
{", ".join(functions)}

## Comment Summary
{", ".join(comments)}
"""
    return content.strip()

def GenerateREADME(repoURL, repoFiles):
    repoName, imports, funcs, comments = AnalyzeRepository(repoURL, repoFiles)
    prompt = GeneratePrompt(repoName, imports, funcs, comments)

    print("==== GeneratePrompt가 만든 프롬프트 내용 ====")
    print(prompt)

    response = requests.post(
        VLLM_SERVER_URL,
        headers={"Content-Type": "application/json"},
        json={
            "model": "google/gemma-3-4b-it",
            "messages": [
                {
                    "role": "system",
                    "content": (
                    "You are a professional technical writer for GitHub repositories.\n"
                    "Given information about a codebase (e.g., imports, functions, comments), write a clear and informative document in valid Markdown format.\n"
                    "**Never wrap the entire output in any code fences like ```markdown or ``` — just output raw Markdown.**\n"
                    "Focus on technical clarity, clean structure, and helpful formatting.\n"
                    "**must include** the following sections, in order:\n\n"
                    "1. **Repository Name** (as the title)\n"
                    "2. **Descriptions**"
                    "   - Provide a concise but meaningful overview of what this repository does and why it exists.\n"
                    "   - Use hints from the repository name, file names, and code comments to infer the purpose and real-world use case.\n"
                    "   - Avoid vague language — be specific about the problem the project solves or the functionality it offers.\n"
                    "3. **Used Libraries**\n"
                    "   - If the list is extensive, group standard/common libraries together and highlight only the **most relevant or unique libraries**.\n"
                    "   - For each key library, provide a technical explanation of its role in this specific project.\n"
                    "4. **Function Overview**\n"
                    "   - Focus only on the **central or unique functions and classes** in the codebase.\n"
                    "   - Describe what each one does, its inputs and outputs, and how it fits into the overall logic.\n"
                    "   - If there are too many small functions, group or summarize them where appropriate (e.g., \"data loaders\", \"utility helpers\").\n"
                    "   - Avoid generic or boilerplate explanations.\n\n"

                )




                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "temperature": 0.7
        }
    )

    if response.status_code == 200:
        result = response.json()
        readme = result["choices"][0]["message"]["content"]
        return RemoveThink(readme)
    else:
        print("vLLM 요청 실패!")
        print(f"상태 코드: {response.status_code}")
        print("전송한 프롬프트:")
        print(prompt)
        print("응답 내용:")
        print(response.text)
        raise Exception(f"vLLM 요청 실패: {response.status_code} - {response.text}")
