# 1️⃣ 최신 Python 3.10 이미지 사용
FROM python:3.10

# 2️⃣ 작업 디렉토리 설정
WORKDIR /app

# 3️⃣ 의존성 설치 (이미지 빌드를 캐싱하기 위해 requirements.txt만 먼저 복사)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# 4️⃣ 프로젝트 코드 복사
COPY . .

# 5️⃣ 환경 변수 설정
ENV PYTHONPATH=/app/src

# 6️⃣ FastAPI 실행
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]