"""
API 사용량 서비스 모듈
tb_api_usage 테이블에 AI API 호출 이력을 기록하고 통계를 조회한다.
"""
from typing import Optional
from app.database import get_connection
from app.config import AI_TOKEN_PRICING


def calculate_cost(model_name: str, input_tokens: int, output_tokens: int) -> float:
    """
    모델명과 토큰 수로 USD 비용을 계산한다.
    단가 테이블에 없는 모델은 0.0을 반환한다.
    """
    pricing = AI_TOKEN_PRICING.get(model_name)
    if not pricing:
        return 0.0
    input_cost = (input_tokens / 1_000_000) * pricing["input"]
    output_cost = (output_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 6)


def save_usage(
    admin_id: str,
    api_type: str,
    ai_provider: str,
    model_name: str,
    input_tokens: int,
    output_tokens: int,
    exam_key: Optional[int] = None,
) -> None:
    """
    API 사용 이력을 DB에 저장한다.
    비용(cost_usd)은 모델 단가를 기반으로 자동 계산한다.
    """
    cost = calculate_cost(model_name, input_tokens, output_tokens)
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tb_api_usage
                   (admin_id, api_type, ai_provider, model_name, input_tokens, output_tokens, cost_usd, exam_key)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (admin_id, api_type, ai_provider, model_name, input_tokens, output_tokens, cost, exam_key),
        )
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def get_summary_stats() -> dict:
    """
    대시보드 상단 요약 카드용 통계를 조회한다.
    - 총 사용자 수, 등록 시험 수, 등록 문항 수, 금월 API 호출 수
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT
                (SELECT COUNT(*) FROM tb_user WHERE del_yn = 'N') AS total_users,
                (SELECT COUNT(*) FROM tb_exam_list WHERE del_yn = 'N') AS total_exams,
                (SELECT COUNT(*) FROM tb_exam_question WHERE del_yn = 'N') AS total_questions,
                (SELECT COUNT(*) FROM tb_api_usage
                 WHERE ins_date >= DATE_TRUNC('month', CURRENT_DATE)) AS monthly_api_calls
        """)
        row = cursor.fetchone()
        return {
            "total_users": row["total_users"],
            "total_exams": row["total_exams"],
            "total_questions": row["total_questions"],
            "monthly_api_calls": row["monthly_api_calls"],
        }
    finally:
        conn.close()


def get_exam_stats() -> dict:
    """
    시험/문제 현황 통계를 조회한다.
    - 레벨별 시험 수, 영역별 문항 수, 피드백 생성률
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        # 레벨별 시험 수
        cursor.execute("""
            SELECT COALESCE(c.code_name, e.tpk_level) AS label, COUNT(*) AS count
              FROM tb_exam_list e
              LEFT JOIN tb_code c ON c.group_code = 'tpk_level' AND c.code = CAST(e.tpk_level AS INTEGER)
             WHERE e.del_yn = 'N'
             GROUP BY label
             ORDER BY count DESC
        """)
        level_dist = [{"label": r["label"], "count": r["count"]} for r in cursor.fetchall()]

        # 영역별 문항 수
        cursor.execute("""
            SELECT COALESCE(c.code_name, q.section) AS label, COUNT(*) AS count
              FROM tb_exam_question q
              LEFT JOIN tb_code c ON c.group_code = 'section' AND CAST(c.code AS VARCHAR) = q.section
             WHERE q.del_yn = 'N'
             GROUP BY label
             ORDER BY count DESC
        """)
        section_dist = [{"label": r["label"], "count": r["count"]} for r in cursor.fetchall()]

        # 피드백 생성률
        cursor.execute("""
            SELECT COUNT(*) AS total,
                   COUNT(CASE WHEN feedback_json IS NOT NULL AND feedback_json != '' THEN 1 END) AS with_feedback
              FROM tb_exam_question
             WHERE del_yn = 'N'
        """)
        fb = cursor.fetchone()
        feedback_rate = round((fb["with_feedback"] / fb["total"] * 100) if fb["total"] > 0 else 0, 1)

        return {
            "level_distribution": level_dist,
            "section_distribution": section_dist,
            "feedback_rate": feedback_rate,
            "feedback_total": fb["total"],
            "feedback_done": fb["with_feedback"],
        }
    finally:
        conn.close()


def get_api_usage_stats(period: str = "daily") -> dict:
    """
    API 토큰 사용 이력 통계를 조회한다.
    period: 'daily' (최근 30일), 'weekly' (최근 12주), 'monthly' (최근 12개월)
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()

        if period == "weekly":
            date_trunc = "week"
            limit_days = 84
        elif period == "monthly":
            date_trunc = "month"
            limit_days = 365
        else:
            date_trunc = "day"
            limit_days = 30

        # 일자별/주별/월별 토큰 사용량 + 비용
        cursor.execute(f"""
            SELECT DATE_TRUNC('{date_trunc}', ins_date)::DATE AS period_date,
                   ai_provider,
                   SUM(input_tokens) AS input_tokens,
                   SUM(output_tokens) AS output_tokens,
                   SUM(cost_usd) AS cost_usd,
                   COUNT(*) AS call_count
              FROM tb_api_usage
             WHERE ins_date >= CURRENT_DATE - INTERVAL '{limit_days} days'
             GROUP BY period_date, ai_provider
             ORDER BY period_date ASC
        """)
        rows = cursor.fetchall()
        chart_data = [
            {
                "date": str(r["period_date"]),
                "ai_provider": r["ai_provider"],
                "input_tokens": r["input_tokens"],
                "output_tokens": r["output_tokens"],
                "cost_usd": float(r["cost_usd"]),
                "call_count": r["call_count"],
            }
            for r in rows
        ]

        # 프로바이더별 합계
        cursor.execute(f"""
            SELECT ai_provider,
                   SUM(input_tokens) AS input_tokens,
                   SUM(output_tokens) AS output_tokens,
                   SUM(cost_usd) AS cost_usd,
                   COUNT(*) AS call_count
              FROM tb_api_usage
             WHERE ins_date >= CURRENT_DATE - INTERVAL '{limit_days} days'
             GROUP BY ai_provider
        """)
        provider_summary = [
            {
                "ai_provider": r["ai_provider"],
                "input_tokens": r["input_tokens"],
                "output_tokens": r["output_tokens"],
                "cost_usd": float(r["cost_usd"]),
                "call_count": r["call_count"],
            }
            for r in cursor.fetchall()
        ]

        # 최근 API 호출 목록 (10건)
        cursor.execute("""
            SELECT usage_key, admin_id, api_type, ai_provider, model_name,
                   input_tokens, output_tokens, cost_usd,
                   TO_CHAR(ins_date, 'YYYY-MM-DD HH24:MI:SS') AS ins_date
              FROM tb_api_usage
             ORDER BY ins_date DESC
             LIMIT 10
        """)
        recent = [
            {**r, "cost_usd": float(r["cost_usd"])} for r in cursor.fetchall()
        ]

        return {
            "chart_data": chart_data,
            "provider_summary": provider_summary,
            "recent_calls": recent,
        }
    finally:
        conn.close()
