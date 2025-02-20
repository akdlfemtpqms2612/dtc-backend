from fastapi import FastAPI, HTTPException, Query, Body
from fastapi.middleware.cors import CORSMiddleware
import psycopg2
import os
from dotenv import load_dotenv

# ✅ 환경 변수 로드
load_dotenv()

# ✅ FastAPI 앱 초기화
app = FastAPI()

# ✅ CORS 설정 (배포 시 특정 도메인만 허용하는 것이 좋음)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # 배포 시 특정 도메인으로 변경 권장
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ✅ PostgreSQL 데이터베이스 설정 (환경 변수 사용)
DB_CONFIG = {
    "dbname": os.getenv("DB_NAME", "vehicle_db_utf8"),
    "user": os.getenv("DB_USER", "postgres"),
    "password": os.getenv("DB_PASSWORD", "password2612"),
    "host": os.getenv("DB_HOST", "localhost"),
    "port": os.getenv("DB_PORT", "5432"),
}

# ✅ 데이터베이스 연결 함수 (환경 변수 누락 시 대비)
def get_db_connection():
    """PostgreSQL DB 연결"""
    try:
        return psycopg2.connect(**DB_CONFIG)
    except Exception as e:
        print("❌ DB 연결 오류:", e)
        raise HTTPException(status_code=500, detail="🚨 데이터베이스 연결 실패")

# ✅ 기본 라우트 (서버 상태 확인용)
@app.get("/")
def read_root():
    return {"message": "🚀 FastAPI 서버가 정상 실행 중입니다!"}

# ✅ 차량 목록 가져오기 (GET)
@app.get("/vehicles")
def get_vehicles():
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, name, model FROM vehicles;")
                vehicles = cursor.fetchall()
        return {"vehicles": [{"id": v[0], "name": v[1], "model": v[2]} for v in vehicles]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"🚨 차량 데이터를 불러오는 중 오류 발생: {e}")

# ✅ 차량 추가 (POST) - `Query`에서 `Body`로 변경 (더 안전한 방식)
@app.post("/vehicles")
def add_vehicle(name: str = Body(...), model: str = Body(...)):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("INSERT INTO vehicles (name, model) VALUES (%s, %s) RETURNING id;", (name, model))
                new_id = cursor.fetchone()[0]
            conn.commit()
        return {"id": new_id, "message": "🚗 차량이 성공적으로 추가되었습니다!"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"🚨 차량 추가 중 오류 발생: {e}")

# ✅ 특정 차량 조회 (GET)
@app.get("/vehicles/{vehicle_id}")
def get_vehicle_by_id(vehicle_id: int):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT id, name, model FROM vehicles WHERE id = %s;", (vehicle_id,))
                vehicle = cursor.fetchone()
        if vehicle:
            return {"id": vehicle[0], "name": vehicle[1], "model": vehicle[2]}
        raise HTTPException(status_code=404, detail="🚨 차량을 찾을 수 없습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"🚨 차량 조회 중 오류 발생: {e}")

# ✅ 차량 삭제 (DELETE) - `fetchone()`이 `None`일 경우 예외 방지
@app.delete("/vehicles/{vehicle_id}")
def delete_vehicle(vehicle_id: int):
    try:
        with get_db_connection() as conn:
            with conn.cursor() as cursor:
                cursor.execute("DELETE FROM vehicles WHERE id = %s RETURNING id;", (vehicle_id,))
                deleted_id = cursor.fetchone()
            conn.commit()
        if deleted_id:
            return {"message": f"🚗 차량 ID {vehicle_id} 삭제 완료"}
        else:
            raise HTTPException(status_code=404, detail="🚨 삭제할 차량을 찾을 수 없습니다.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"🚨 차량 삭제 중 오류 발생: {e}")

# ✅ DTC 코드 검색 엔드포인트 (GET)
@app.get("/dtc/{code}")
def get_dtc_info(code: str):
    """DTC(고장 코드) 조회"""
    dtc_info = {
        "P0420": "Catalyst System Efficiency Below Threshold (Bank 1)",
        "P0171": "System Too Lean (Bank 1)",
        "P0300": "Random/Multiple Cylinder Misfire Detected",
    }
    description = dtc_info.get(code.upper())  # 대소문자 구분 없이 검색
    if not description:
        raise HTTPException(status_code=404, detail="⚠ 알 수 없는 DTC 코드입니다.")
    return {"code": code.upper(), "description": description}

# ✅ 서버 실행 (uvicorn)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)
