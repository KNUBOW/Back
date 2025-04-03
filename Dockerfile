# 1️⃣ 최신 Python 3.10 이미지
FROM python:3.10

# 2️⃣ 작업 디렉토리 설정
WORKDIR /app

# 3️⃣ 의존성 설치 (캐싱을 위해 requirements.txt만 먼저 복사)
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# ✅ 4️⃣ 시간대 설정 (tzdata 설치 후 Asia/Seoul 설정)
RUN apt-get update && \
    apt-get install -y tzdata && \
    ln -sf /usr/share/zoneinfo/Asia/Seoul /etc/localtime && \
    echo "Asia/Seoul" > /etc/timezone && \
    apt-get clean

# 5️⃣ 프로젝트 전체 복사
COPY . .

# 6️⃣ 환경 변수 설정
ENV PYTHONPATH=/app/src

# 7️⃣ FastAPI 실행
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000", "--lifespan on"]
