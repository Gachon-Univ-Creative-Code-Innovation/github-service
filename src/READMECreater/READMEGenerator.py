import os
from groq import Groq
from dotenv import load_dotenv
from src.READMECreater.CodeAnalyzer import SummarizeKeywords
from src.READMECreater.CodeAnalyzer import AnalyzeRepository

envPath = os.path.join(os.path.dirname(__file__), "..", "..", ".env")
load_dotenv(dotenv_path=os.path.abspath(envPath))

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
# GROQ API를 사용하여 README 생성
client = Groq(api_key=GROQ_API_KEY)


# README 생성 프롬프트 생성 함수
def GeneratePrompt(repoName, imports, functions, comments):
    # None 값이 포함되지 않도록 필터링
    imports = [imp for imp in imports if imp]
    functions = [func for func in functions if func]
    comments = [cmt for cmt in comments if cmt]

    # 중복 제거
    imports = list(set(imports))
    functions = SummarizeKeywords(functions)
    comments = sorted(comments, key=len, reverse=True)[:5]

    # 프롬프트 생성
    prompt = f"""You are an AI that reviews GitHub repositories and generates README files.
Analyze the following repository and generate a concise README.

Repository : {repoName}

## Used Libraries
{", ".join(imports) if imports else "No external libraries found."}

## Function Overview
{", ".join(functions)}

## Comment Summary
{", ".join(comments)}

Generate a structured README based on the provided information.
"""
    return prompt


# README 생성 함수
def GenerateREADME(repoURL, repoFiles):
    repoName, imports, funcs, comments = AnalyzeRepository(repoURL, repoFiles)
    prompt = GeneratePrompt(repoName, imports, funcs, comments)

    chat = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}], model="qwen-2.5-coder-32b"
    )
    return chat.choices[0].message.content
