from groq import Groq
from .CodeAnalyzer import SummarizeKeywords
from .CodeAnalyzer import AnalyzeRepository

GROQ_API_KEY = "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"
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
def GenerateREADME(repo_url, repo_files):
    repo_name, imports, funcs, comments = AnalyzeRepository(repo_url, repo_files)
    prompt = GeneratePrompt(repo_name, imports, funcs, comments)

    chat = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}], model="qwen-2.5-coder-32b"
    )
    return chat.choices[0].message.content
