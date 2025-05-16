FROM python:3.11-slim

# 실행 위치 설정
WORKDIR /app

# 위치 지정
ENV PYTHONPATH=/app

# 캐시 최적화
# 라이브러리 설치
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 필요한 파일 복사
COPY . .

EXPOSE 8080

# FastAPI 실행
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
