"""
테이블 생성 스크립트
tb_group_code, tb_code는 이미 존재하므로 제외.
나머지 11개 테이블을 FK 의존성 순서대로 생성한다.
psycopg v3를 사용하며, DB 접속정보는 backend/.env에서 로드한다.
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
    # 1. tb_user : 사용자
    """
    CREATE TABLE tb_user (
        user_key      SERIAL       NOT NULL,
        email         VARCHAR(100) NOT NULL,
        provider_id   VARCHAR(100),
        provider_type VARCHAR(20),
        del_yn        VARCHAR(1)   NOT NULL DEFAULT 'N',
        ins_date      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        ins_user      VARCHAR(50)  NOT NULL DEFAULT 'admin',
        upd_date      TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        upd_user      VARCHAR(50)  NOT NULL DEFAULT 'admin',
        CONSTRAINT pk_user PRIMARY KEY (user_key)
    )
    """,

    # 2. tb_question_structure : 문항 구조
    """
    CREATE TABLE tb_question_structure (
        struct_key     SERIAL       NOT NULL,
        struct_name    VARCHAR(50),
        struct_json    TEXT,
        struct_json_ex TEXT,
        del_yn         VARCHAR(1)   NOT NULL DEFAULT 'N',
        ins_date       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        ins_user       VARCHAR(50)  NOT NULL DEFAULT 'admin',
        upd_date       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        upd_user       VARCHAR(50)  NOT NULL DEFAULT 'admin',
        CONSTRAINT pk_question_structure PRIMARY KEY (struct_key)
    )
    """,

    # 3. tb_exam_list : 시험 목록
    """
    CREATE TABLE tb_exam_list (
        exam_key    SERIAL       NOT NULL,
        exam_type   VARCHAR(20)  NOT NULL,
        round       INTEGER,
        tpk_level   VARCHAR(10),
        del_yn      VARCHAR(1)   NOT NULL DEFAULT 'N',
        ins_date    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        ins_user    VARCHAR(50)  NOT NULL DEFAULT 'admin',
        upd_date    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        upd_user    VARCHAR(50)  NOT NULL DEFAULT 'admin',
        CONSTRAINT pk_exam_list PRIMARY KEY (exam_key)
    )
    """,

    # 4. tb_exam_file : 시험 파일
    """
    CREATE TABLE tb_exam_file (
        pdf_key     SERIAL        NOT NULL,
        exam_key    INTEGER       NOT NULL,
        file_name   VARCHAR(255)  NOT NULL,
        file_path   VARCHAR(500)  NOT NULL,
        file_size   INTEGER,
        sort_order  INTEGER       DEFAULT 0,
        file_type   VARCHAR(20),
        del_yn      VARCHAR(1)    NOT NULL DEFAULT 'N',
        ins_date    TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
        ins_user    VARCHAR(50)   NOT NULL DEFAULT 'admin',
        CONSTRAINT pk_exam_file PRIMARY KEY (pdf_key),
        CONSTRAINT fk_exam_file_exam FOREIGN KEY (exam_key) REFERENCES tb_exam_list(exam_key)
    )
    """,

    # 5. tb_user_device : 사용자 디바이스
    """
    CREATE TABLE tb_user_device (
        user_key    INTEGER      NOT NULL,
        seq         SERIAL       NOT NULL,
        device_type VARCHAR(20),
        device_name VARCHAR(50),
        os          VARCHAR(20),
        version     VARCHAR(20),
        del_yn      VARCHAR(1)   NOT NULL DEFAULT 'N',
        ins_date    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        ins_user    VARCHAR(50)  NOT NULL DEFAULT 'admin',
        upd_date    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        upd_user    VARCHAR(50)  NOT NULL DEFAULT 'admin',
        CONSTRAINT pk_user_device PRIMARY KEY (user_key, seq),
        CONSTRAINT fk_user_device_user FOREIGN KEY (user_key) REFERENCES tb_user(user_key)
    )
    """,

    # 5. tb_exam_instruction : 지시문
    """
    CREATE TABLE tb_exam_instruction (
        exam_key    INTEGER      NOT NULL,
        ins_no      INTEGER      NOT NULL,
        ins_json    TEXT,
        del_yn      VARCHAR(1)   NOT NULL DEFAULT 'N',
        ins_date    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        ins_user    VARCHAR(50)  NOT NULL DEFAULT 'admin',
        upd_date    TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        upd_user    VARCHAR(50)  NOT NULL DEFAULT 'admin',
        CONSTRAINT pk_exam_instruction PRIMARY KEY (exam_key, ins_no),
        CONSTRAINT fk_exam_instruction_exam FOREIGN KEY (exam_key) REFERENCES tb_exam_list(exam_key)
    )
    """,

    # 6. tb_exam_question : 시험문항
    """
    CREATE TABLE tb_exam_question (
        exam_key       INTEGER      NOT NULL,
        question_no    INTEGER      NOT NULL,
        section        VARCHAR(20),
        question_type  VARCHAR(20),
        struct_type    VARCHAR(20),
        question_json  TEXT,
        feedback_json  TEXT,
        score          INTEGER,
        difficulty     VARCHAR(10),
        del_yn         VARCHAR(1)   NOT NULL DEFAULT 'N',
        ins_date       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        ins_user       VARCHAR(50)  NOT NULL DEFAULT 'admin',
        upd_date       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        upd_user       VARCHAR(50)  NOT NULL DEFAULT 'admin',
        CONSTRAINT pk_exam_question PRIMARY KEY (exam_key, question_no),
        CONSTRAINT fk_exam_question_exam FOREIGN KEY (exam_key) REFERENCES tb_exam_list(exam_key)
    )
    """,

    # 7. tb_exam_answer : 시험 정답
    """
    CREATE TABLE tb_exam_answer (
        exam_key       INTEGER      NOT NULL,
        question_no    INTEGER      NOT NULL,
        feedback_json  TEXT,
        del_yn         VARCHAR(1)   NOT NULL DEFAULT 'N',
        ins_date       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        ins_user       VARCHAR(50)  NOT NULL DEFAULT 'admin',
        upd_date       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        upd_user       VARCHAR(50)  NOT NULL DEFAULT 'admin',
        CONSTRAINT pk_exam_answer PRIMARY KEY (exam_key, question_no),
        CONSTRAINT fk_exam_answer_question FOREIGN KEY (exam_key, question_no) REFERENCES tb_exam_question(exam_key, question_no)
    )
    """,

    # 8. tb_practice_question : 연습 문항
    """
    CREATE TABLE tb_practice_question (
        question_no    SERIAL       NOT NULL,
        section        VARCHAR(20),
        question_type  VARCHAR(20),
        struct_type    VARCHAR(20),
        question_json  TEXT,
        score          INTEGER,
        difficulty     VARCHAR(10),
        confirm_yn     VARCHAR(1)   DEFAULT 'N',
        del_yn         VARCHAR(1)   NOT NULL DEFAULT 'N',
        ins_date       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        ins_user       VARCHAR(50)  NOT NULL DEFAULT 'admin',
        upd_date       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        upd_user       VARCHAR(50)  NOT NULL DEFAULT 'admin',
        CONSTRAINT pk_practice_question PRIMARY KEY (question_no)
    )
    """,

    # 9. tb_practice_answer : 연습 문항 정답
    """
    CREATE TABLE tb_practice_answer (
        question_no    INTEGER      NOT NULL,
        feedback_json  TEXT,
        del_yn         VARCHAR(1)   NOT NULL DEFAULT 'N',
        ins_date       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        ins_user       VARCHAR(50)  NOT NULL DEFAULT 'admin',
        upd_date       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        upd_user       VARCHAR(50)  NOT NULL DEFAULT 'admin',
        CONSTRAINT pk_practice_answer PRIMARY KEY (question_no),
        CONSTRAINT fk_practice_answer_question FOREIGN KEY (question_no) REFERENCES tb_practice_question(question_no)
    )
    """,

    # 10. tb_history_exam : 학습 이력 - 시험
    """
    CREATE TABLE tb_history_exam (
        history_key    SERIAL       NOT NULL,
        user_key       INTEGER      NOT NULL,
        exam_key       INTEGER      NOT NULL,
        question_no    INTEGER      NOT NULL,
        history_type   VARCHAR(20),
        result_json    TEXT,
        duration       INTEGER,
        del_yn         VARCHAR(1)   NOT NULL DEFAULT 'N',
        ins_date       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        ins_user       VARCHAR(50)  NOT NULL DEFAULT 'admin',
        upd_date       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        upd_user       VARCHAR(50)  NOT NULL DEFAULT 'admin',
        CONSTRAINT pk_history_exam PRIMARY KEY (history_key),
        CONSTRAINT fk_history_exam_user FOREIGN KEY (user_key) REFERENCES tb_user(user_key),
        CONSTRAINT fk_history_exam_question FOREIGN KEY (exam_key, question_no) REFERENCES tb_exam_question(exam_key, question_no)
    )
    """,

    # 11. tb_history_practice : 학습 이력 - 연습
    """
    CREATE TABLE tb_history_practice (
        history_key    SERIAL       NOT NULL,
        user_key       INTEGER      NOT NULL,
        question_no    INTEGER      NOT NULL,
        history_type   VARCHAR(20),
        result_json    TEXT,
        duration       INTEGER,
        del_yn         VARCHAR(1)   NOT NULL DEFAULT 'N',
        ins_date       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        ins_user       VARCHAR(50)  NOT NULL DEFAULT 'admin',
        upd_date       TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
        upd_user       VARCHAR(50)  NOT NULL DEFAULT 'admin',
        CONSTRAINT pk_history_practice PRIMARY KEY (history_key),
        CONSTRAINT fk_history_practice_user FOREIGN KEY (user_key) REFERENCES tb_user(user_key),
        CONSTRAINT fk_history_practice_question FOREIGN KEY (question_no) REFERENCES tb_practice_question(question_no)
    )
    """
]

try:
    for i, sql in enumerate(sqls, 1):
        # 테이블명 추출
        tbl_name = sql.strip().split("(")[0].split()[-1]
        cur.execute(sql)
        print(f"[{i}/11] {tbl_name} 생성 완료")

    conn.commit()
    print("\n모든 테이블 생성 성공! (COMMIT 완료)")

    # 최종 테이블 목록 확인
    cur.execute("""
        SELECT table_name FROM information_schema.tables
        WHERE table_schema = 'public' ORDER BY table_name
    """)
    print("\n=== 전체 테이블 목록 ===")
    for row in cur.fetchall():
        print(f"  - {row[0]}")

except Exception as e:
    conn.rollback()
    print(f"\n오류 발생 (ROLLBACK): {e}")

finally:
    cur.close()
    conn.close()
