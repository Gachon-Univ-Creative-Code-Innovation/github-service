import re
import ast
from collections import Counter
from .GithubFetcher import GetLanguageExtensions


# 공통 주석 추출 함수
def ExtractComments(code, singleComment, multiComment):
    # 단일 주석 추출
    singleLineComments = re.findall(singleComment, code, re.MULTILINE)
    # 다중 주석 추출
    MultiLineComments = re.findall(multiComment, code, re.DOTALL)
    return singleLineComments + [c.strip() for c in MultiLineComments]


# Python 코드 분석
def AnalyzePythonCode(code):
    # Python AST를 사용하여 코드 분석
    tree = ast.parse(code)
    # import 및 from import 구문 추출
    imports = [
        node.names[0].name for node in ast.walk(tree) if isinstance(node, ast.Import)
    ]
    froms = [node.module for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
    imports.extend(froms)

    # 함수 정의 추출
    functions = [
        node.name for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)
    ]
    # 주석 추출
    comments = ExtractComments(code, r"#(.*)", r'""".*?"""|\'\'\'.*?\'\'\'')

    return imports, functions, comments


""" Python을 제외하곤 AST를 사용하지 않고 정규 표현식으로 분석합니다.
    - 이유 : Python은 AST를 사용하여 코드 구조를 더 정확하게 분석할 수 있지만,
    나머지 언어들은 외부 라이브러리 사용 시 설치가 필요하고, 복잡도가 증가합니다.
"""


# Java 코드 분석
def AnalyzeJavaCode(code):
    imports = re.findall(r"import\s+([\w.]+);", code)
    functions = re.findall(r"\s+(\w+)\s*\(.*\)\s*\{", code)
    comments = ExtractComments(code, r"//(.*)", r"/\*.*?\*/")
    return imports, functions, comments


# JavaScript/TypeScript 코드 분석
def AnalyzeJSCode(code):
    imports = re.findall(r"import\s+.*?from\s+['\"](.*?)['\"]", code)
    functions = re.findall(r"function\s+(\w+)|(\w+)\s*=\s*\(?.*?\)?\s*=>", code)
    functions = [f[0] if f[0] else f[1] for f in functions]
    comments = ExtractComments(code, r"//(.*)", r"/\*.*?\*/")
    return imports, functions, comments


# C, C++, C# 코드 분석
def AnalyzeCCode(code):
    imports = re.findall(r"#include\s+<(.*?)>", code)
    functions = re.findall(r"\b\w+\s+(\w+)\s*\(.*?\)\s*\{", code)
    comments = ExtractComments(code, r"//(.*)", r"/\*.*?\*/")
    return imports, functions, comments


# Go 코드 분석
def AnalyzeGoCode(code):
    imports = re.findall(r"import\s+\"(.*?)\"", code)
    functions = re.findall(r"func\s+(\w+)\s*\(", code)
    comments = ExtractComments(code, r"//(.*)", r"/\*.*?\*/")
    return imports, functions, comments


# PHP 코드 분석
def AnalyzePhpCode(code):
    imports = re.findall(r"require(_once)?\s*\(?['\"](.*?)['\"]\)?;", code)
    functions = re.findall(r"function\s+(\w+)\s*\(", code)
    comments = ExtractComments(code, r"//(.*)", r"/\*.*?\*/")
    return [imp[1] for imp in imports], functions, comments


# Ruby 코드 분석
def AnalyzeRubyCode(code):
    imports = re.findall(r"require\s+['\"](.*?)['\"]", code)
    functions = re.findall(r"def\s+(\w+)", code)
    comments = ExtractComments(code, r"#(.*)", r"=begin(.*?)=end")
    return imports, functions, comments


# 키워드 기반 요약 함수 중복 제거 및 요약 (n개 선택)
def SummarizeKeywords(items, maxCategories=30):
    if not items:
        return ["No items found."]

    keywordCount = Counter()

    for item in items:
        words = re.findall(r"\b\w+\b", item)  # 단어 추출
        for word in words:
            keywordCount[word.lower()] += 1  # 빈도수 계산

    # 가장 많이 등장하는 키워드 top N개 선택
    commonKeywords = [word for word, _ in keywordCount.most_common(maxCategories)]

    # 최종 요약 문장 생성
    summary = ", ".join(commonKeywords)
    if len(items) > maxCategories:
        summary += f", and {len(items) - maxCategories} more..."

    return [summary]


# 저장소 파일 분석 함수
def AnalyzeRepository(repoName, repoFiles):
    allImports, allFunctions, allComments = set(), set(), set()
    langExts = GetLanguageExtensions()

    for fileName, fileContent in repoFiles:
        for lang, extensions in langExts.items():
            if isinstance(extensions, str):
                extensions = [extensions]
            if any(fileName.endswith(ext) for ext in extensions):
                if lang == "python":
                    imports, functions, comments = AnalyzePythonCode(fileContent)
                elif lang == "java":
                    imports, functions, comments = AnalyzeJavaCode(fileContent)
                elif lang in ["javascript", "typescript"]:
                    imports, functions, comments = AnalyzeJSCode(fileContent)
                elif lang in ["c", "cpp", "csharp"]:
                    imports, functions, comments = AnalyzeCCode(fileContent)
                elif lang == "go":
                    imports, functions, comments = AnalyzeGoCode(fileContent)
                elif lang == "php":
                    imports, functions, comments = AnalyzePhpCode(fileContent)
                elif lang == "ruby":
                    imports, functions, comments = AnalyzeRubyCode(fileContent)
                else:
                    continue

                allImports.update(imports)
                allFunctions.update(functions)
                allComments.update(comments)

    return repoName, allImports, allFunctions, allComments
