from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import psycopg2

app = FastAPI()

# ✅ CORS 설정 (프론트엔드에서 API 요청 가능하도록 허용)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 모든 도메인에서 요청 허용
    allow_credentials=True,
    allow_methods=["*"],  # 모든 HTTP 메서드 허용
    allow_headers=["*"],  # 모든 헤더 허용
)

# ✅ PostgreSQL 데이터베이스 연결 설정
DB_CONFIG = {
    "dbname": "vehicle_db_utf8",
    "user": "postgres",
    "password": "password2612",
    "host": "localhost",
    "port": "5432"
}

def get_db_connection():
    """ PostgreSQL DB 연결 """
    return psycopg2.connect(**DB_CONFIG)

# ✅ 기본 루트
@app.get("/")
def read_root():
    return {"message": "🚀 FastAPI is running successfully!"}

# ✅ DTC 코드 조회 API
@app.get("/dtc/{code}")
def get_dtc_info(code: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    query = """
        SELECT dtc_codes.dtc_code, dtc_codes.category, dtc_codes.description, dtc_solutions.solution 
        FROM dtc_codes 
        LEFT JOIN dtc_solutions ON dtc_codes.dtc_code = dtc_solutions.dtc_code 
        WHERE LOWER(dtc_codes.dtc_code) = LOWER(%s);
    """

    cursor.execute(query, (code,))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    if results:
        unique_solutions = list(dict.fromkeys(row[3] for row in results if row[3]))

        return {
            "dtc_code": results[0][0],
            "category": results[0][1],
            "description": results[0][2],
            "solutions": unique_solutions
        }
    else:
        raise HTTPException(status_code=404, detail=f"DTC 코드 '{code}'가 데이터베이스에 없습니다.")

# ✅ DTC 코드 자동완성 검색 기능
@app.get("/dtc/search/{query}")
def search_dtc_code(query: str):
    conn = get_db_connection()
    cursor = conn.cursor()

    query_sql = "SELECT dtc_code FROM dtc_codes WHERE dtc_code ILIKE %s LIMIT 10;"
    cursor.execute(query_sql, (f"%{query}%",))
    results = cursor.fetchall()

    cursor.close()
    conn.close()

    return {"suggestions": [row[0] for row in results]}

# ✅ 사용자 맞춤 인사 엔드포인트
@app.get("/hello/{name}")
def read_item(name: str):
    return {"message": f"안녕하세요, {name}님! FastAPI로 만든 API입니다. 😊"}

# ✅ FastAPI 실행 (로컬 개발 환경)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
