"""
마이그레이션: tb_practice_list 테이블 추가 및 tb_practice_question 컬럼 추가

변경 내용:
  1. tb_practice_list 신규 생성
     - 연습문제 묶음 관리 테이블 (tb_exam_list와 대칭 구조)
     - tb_practice_request의 결과물 묶음을 참조
  2. tb_practice_question에 practice_key 컬럼 추가
     - tb_practice_list FK 연결

실행 전제: tb_practice_request, tb_practice_question 테이블이 이미 존재해야 함
"""
import os
import sys
from dotenv import load_dotenv
import psycopg

# backend/.env 파일에서 DB 접속정보 로드
env_path = os.path.join(os.path.dirname(__file__), "..", "backend", ".env")
load_dotenv(env_path)

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = os.getenv("DB_PORT", "5432")
DB_NAME = os.getenv("DB_NAME", "tpk_db")
DB_USER = os.getenv("DB_USER", "tpk")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

conn = psycopg.connect(DATABASE_URL, autocommit=False)
cur = conn.cursor()

sqls = [
    # 1. tb_practice_list : 연습문제 묶음
    # tb_exam_list와 대칭 구조. tb_practice_request의 결과물을 묶는 단위.
    # request_key는 AI/수동 생성 요청으로 만들어진 경우 참조, 수동 직접 등록이면 NULL 허용.
    (
        "tb_practice_list 테이블 생성",
        """
        CREATE TABLE IF NOT EXISTS tb_practice_list (
            practice_key  SERIAL       NOT NULL,
            request_key   INTEGER,
            exam_type     VARCHAR(20)  NOT NULL,
            tpk_level     VARCHAR(10),
            section       VARCHAR(20),
            del_yn        VARCHAR(1)   NOT NULL DEFAULT 'N',
            ins_date      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
            ins_user      VARCHAR(50)  NOT NULL DEFAULT 'admin',
            upd_date      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
            upd_user      VARCHAR(50)  NOT NULL DEFAULT 'admin',
            CONSTRAINT pk_practice_list PRIMARY KEY (practice_key),
            CONSTRAINT fk_practice_list_request
                FOREIGN KEY (request_key) REFERENCES tb_practice_request(request_key)
        )
        """
    ),

    # 2. tb_practice_question에 practice_key 컬럼 추가
    # 연습문항이 어느 묶음(tb_practice_list)에 속하는지 FK로 연결
    (
        "tb_practice_question에 practice_key 컬럼 추가",
        """
        ALTER TABLE tb_practice_question
        ADD COLUMN IF NOT EXISTS practice_key INTEGER,
        ADD CONSTRAINT fk_practice_question_list
            FOREIGN KEY (practice_key) REFERENCES tb_practice_list(practice_key)
        """
    ),
]

try:
    for desc, sql in sqls:
        cur.execute(sql)
        print(f"[완료] {desc}")

    conn.commit()
    print("\n마이그레이션 성공! (COMMIT 완료)")

except Exception as e:
    conn.rollback()
    print(f"\n오류 발생 (ROLLBACK): {e}")
    sys.exit(1)

finally:
    cur.close()
    conn.close()
