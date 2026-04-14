"""
시험 이미지 crop 서비스 모듈
PDF 페이지에서 OpenCV를 이용하여 그림 영역(일러스트, 광고, 그래프 등)을 자동 검출하고 crop한다.
검출된 이미지를 Cloudflare R2에 업로드한다.
"""
import os
import cv2
import numpy as np
import fitz  # PyMuPDF
from PIL import Image
from io import BytesIO

from app.database import get_connection
from app.services import r2_storage


def _get_pdf_file_info(exam_key: int, pdf_key: int) -> dict:
    """
    PDF 파일 정보를 조회한다.

    Args:
        exam_key: 시험 PK
        pdf_key: PDF 파일 PK

    Returns:
        파일 정보 딕셔너리 (file_path, file_name 포함)

    Raises:
        ValueError: 파일이 존재하지 않을 때
    """
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT pdf_key, exam_key, file_name, file_path
              FROM tb_exam_file
             WHERE exam_key = %s AND pdf_key = %s AND del_yn = 'N'
            """,
            (exam_key, pdf_key),
        )
        row = cursor.fetchone()
        if not row:
            raise ValueError("PDF 파일을 찾을 수 없습니다.")
        return row
    finally:
        conn.close()


def _r2_image_key(exam_key: int, filename: str) -> str:
    """R2 오브젝트 키를 생성한다. (exam/{exam_key}/{filename})"""
    return f"exam/{exam_key}/{filename}"


def _pdf_page_to_cv2(doc, page_num: int, dpi: int = 300):
    """
    PDF 페이지를 OpenCV 이미지(numpy array)로 변환한다.

    Args:
        doc: fitz.Document 객체
        page_num: 페이지 번호 (0-based)
        dpi: 렌더링 해상도

    Returns:
        OpenCV BGR 이미지 (numpy array)
    """
    page = doc[page_num]
    pix = page.get_pixmap(dpi=dpi)
    img_pil = Image.open(BytesIO(pix.tobytes("png")))
    img_cv = cv2.cvtColor(np.array(img_pil), cv2.COLOR_RGB2BGR)
    return img_cv


def _find_image_boxes(img_cv, min_area: int = 150000, max_area: int = 1500000) -> list[tuple]:
    """
    OpenCV 다중 임계값 방식으로 이미지 영역(테두리 박스)을 검출한다.
    - 방법1: 일반 이진화 (진한 테두리)
    - 방법2: 낮은 임계값 (연한 그라데이션 배경 포함)
    - 방법3: 적응적 이진화 (다양한 밝기 대응)

    Args:
        img_cv: OpenCV BGR 이미지
        min_area: 최소 면적 (이하 무시)
        max_area: 최대 면적 (이상 무시)

    Returns:
        검출된 박스 리스트 [(x, y, w, h, area), ...]  — y좌표 오름차순 정렬
    """
    gray = cv2.cvtColor(img_cv, cv2.COLOR_BGR2GRAY)
    h, w = gray.shape
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))

    # 3가지 이진화 방법으로 윤곽선 검출
    thresh_list = []

    # 방법1: 일반 이진화 (진한 테두리)
    _, t1 = cv2.threshold(gray, 200, 255, cv2.THRESH_BINARY_INV)
    thresh_list.append(cv2.morphologyEx(t1, cv2.MORPH_CLOSE, kernel, iterations=2))

    # 방법2: 낮은 임계값 (연한 그라데이션 배경 포함)
    _, t2 = cv2.threshold(gray, 220, 255, cv2.THRESH_BINARY_INV)
    thresh_list.append(cv2.morphologyEx(t2, cv2.MORPH_CLOSE, kernel, iterations=3))

    # 방법3: 적응적 이진화
    t3 = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                cv2.THRESH_BINARY_INV, 51, 10)
    thresh_list.append(cv2.morphologyEx(t3, cv2.MORPH_CLOSE, kernel, iterations=3))

    all_boxes = []
    for thresh in thresh_list:
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        for cnt in contours:
            area = cv2.contourArea(cnt)
            if area < min_area or area > max_area:
                continue

            x, y, bw, bh = cv2.boundingRect(cnt)
            aspect_ratio = bw / bh

            # 너무 길쭉하거나 페이지 전체인 경우 제외
            if aspect_ratio < 0.3 or aspect_ratio > 5.0:
                continue
            if bw > w * 0.9 and bh > h * 0.9:
                continue

            # 중복 제거: 기존 박스와 IoU 30% 이상이면 스킵
            is_dup = False
            for (ex, ey, ebw, ebh, _) in all_boxes:
                ix1, iy1 = max(x, ex), max(y, ey)
                ix2, iy2 = min(x + bw, ex + ebw), min(y + bh, ey + ebh)
                inter = max(0, ix2 - ix1) * max(0, iy2 - iy1)
                union = bw * bh + ebw * ebh - inter
                if union > 0 and inter / union > 0.3:
                    is_dup = True
                    break
            if not is_dup:
                all_boxes.append((x, y, bw, bh, area))

    # y좌표 → x좌표 순서로 정렬
    all_boxes.sort(key=lambda b: (b[1], b[0]))
    return all_boxes


def _is_image_content(img_cv, x: int, y: int, w: int, h: int) -> bool:
    """
    검출된 박스 내부가 실제 이미지(일러스트/그래프/사진)인지 텍스트인지 판별한다.
    텍스트 영역은 대부분 흰색 배경에 검은 글자이므로:
    - 밝기(평균)가 높고 분산이 낮으면 텍스트 → False
    - 중간톤 픽셀 비율이 높으면 이미지(일러스트/그래프) → True

    Args:
        img_cv: 전체 페이지 OpenCV BGR 이미지
        x, y, w, h: 박스 좌표

    Returns:
        True이면 이미지 콘텐츠, False이면 텍스트 콘텐츠
    """
    roi = img_cv[y:y + h, x:x + w]
    gray_roi = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)

    mean_val = np.mean(gray_roi)
    std_val = np.std(gray_roi)

    # 중간톤 픽셀 비율 (50~200 사이 값): 이미지는 다양한 톤이 많음
    mid_tone_mask = (gray_roi > 50) & (gray_roi < 200)
    mid_tone_ratio = np.sum(mid_tone_mask) / gray_roi.size

    # 실제 이미지(일러스트/그래프/광고): mid > 0.10 또는 std > 80 또는 mean < 220
    # 텍스트 단락: mean > 228, std 60~70, mid < 0.05 — 흰 배경에 검은 글자
    # 광고/안내문(배경 그라데이션 있는 텍스트): mean 210~230, std 55~75, mid 0.05~0.08
    if mid_tone_ratio > 0.10:
        return True   # 중간톤 풍부 → 이미지
    if std_val > 80:
        return True   # 분산 높음 → 이미지
    if mean_val < 220:
        return True   # 평균 밝기 낮음 → 배경이 어두운 이미지/광고
    if mean_val > 228 and std_val < 76 and mid_tone_ratio < 0.045:
        return False  # 흰 배경 + 낮은 분산 + 중간톤 매우 적음 → 텍스트/표지 요소

    return True  # 판별 불확실하면 이미지로 간주


def crop_images_from_pdf(exam_key: int, pdf_key: int) -> list[dict]:
    """
    PDF에서 이미지 영역을 검출하여 crop하고 저장한다.

    Args:
        exam_key: 시험 PK
        pdf_key: PDF 파일 PK

    Returns:
        검출된 이미지 정보 리스트
        [{ "page": 1, "box_index": 1, "filename": "...", "x": ..., "y": ..., "w": ..., "h": ... }, ...]
    """
    # PDF 파일을 R2에서 다운로드
    file_info = _get_pdf_file_info(exam_key, pdf_key)
    r2_key = file_info["file_path"]

    try:
        pdf_bytes = r2_storage.download_bytes(r2_key)
    except FileNotFoundError:
        raise FileNotFoundError(f"PDF 파일이 R2에 존재하지 않습니다: {r2_key}")

    # 메모리에서 PDF 열기
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    results = []

    try:
        for page_num in range(len(doc)):
            # PDF 페이지 → OpenCV 이미지
            img_cv = _pdf_page_to_cv2(doc, page_num, dpi=300)

            # 이미지 박스 검출
            boxes = _find_image_boxes(img_cv)

            if not boxes:
                continue

            # 각 박스를 이미지/텍스트 판별 후 이미지만 crop하여 R2에 업로드
            img_box_idx = 0
            for (x, y, bw, bh, area) in boxes:
                # 텍스트 영역이면 스킵
                if not _is_image_content(img_cv, x, y, bw, bh):
                    continue

                img_box_idx += 1
                filename = f"p{page_num + 1}_box{img_box_idx}.png"

                cropped = img_cv[y:y + bh, x:x + bw]

                # OpenCV 이미지 → PNG 바이트로 인코딩 후 R2 업로드
                success, png_data = cv2.imencode(".png", cropped)
                if success:
                    r2_key_img = _r2_image_key(exam_key, filename)
                    r2_storage.upload_bytes(r2_key_img, png_data.tobytes(), "image/png")

                results.append({
                    "page": page_num + 1,
                    "box_index": img_box_idx,
                    "filename": filename,
                    "x": int(x),
                    "y": int(y),
                    "w": int(bw),
                    "h": int(bh),
                    "area": int(area),
                })
    finally:
        doc.close()

    return results


def rename_crop_image(exam_key: int, old_filename: str, new_filename: str) -> str:
    """
    R2에서 crop된 임시 이미지 파일명을 최종 파일명으로 변경한다. (copy + delete 방식)

    Args:
        exam_key: 시험 PK
        old_filename: 기존 파일명 (예: p1_box1.png)
        new_filename: 최종 파일명 (예: 5_1.png)

    Returns:
        변경된 파일의 R2 키
    """
    old_key = _r2_image_key(exam_key, old_filename)
    new_key = _r2_image_key(exam_key, new_filename)
    r2_storage.rename_object(old_key, new_key)
    return new_key


def batch_rename_crop_images(exam_key: int, rename_map: list[dict]) -> list[dict]:
    """
    여러 crop 이미지 파일명을 일괄 변경한다.

    Args:
        exam_key: 시험 PK
        rename_map: [{ "old_filename": "p1_box1.png", "new_filename": "5_1.png" }, ...]

    Returns:
        변경 결과 리스트 [{ "old_filename": "...", "new_filename": "...", "path": "..." }, ...]
    """
    results = []
    for item in rename_map:
        path = rename_crop_image(exam_key, item["old_filename"], item["new_filename"])
        results.append({
            "old_filename": item["old_filename"],
            "new_filename": item["new_filename"],
            "path": path,
        })
    return results


# ─── 수동 생성 관련 함수 ────────────────────────────────────────────


def get_pdf_page_count(exam_key: int, pdf_key: int) -> int:
    """
    PDF 파일의 총 페이지 수를 반환한다.

    Args:
        exam_key: 시험 PK
        pdf_key: PDF 파일 PK

    Returns:
        페이지 수
    """
    file_info = _get_pdf_file_info(exam_key, pdf_key)
    r2_key = file_info["file_path"]
    pdf_bytes = r2_storage.download_bytes(r2_key)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    count = len(doc)
    doc.close()
    return count


def render_pdf_page_as_png(exam_key: int, pdf_key: int, page: int, dpi: int = 150) -> bytes:
    """
    PDF 특정 페이지를 PNG 이미지 바이트로 변환하여 반환한다.
    수동 생성 팝업에서 PDF를 이미지로 표시하기 위해 사용한다.

    Args:
        exam_key: 시험 PK
        pdf_key: PDF 파일 PK
        page: 페이지 번호 (1-based)
        dpi: 렌더링 해상도 (기본 150 — 화면 표시용)

    Returns:
        PNG 이미지 바이트
    """
    file_info = _get_pdf_file_info(exam_key, pdf_key)
    r2_key = file_info["file_path"]
    pdf_bytes = r2_storage.download_bytes(r2_key)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    try:
        page_num = page - 1  # 1-based → 0-based
        if page_num < 0 or page_num >= len(doc):
            raise ValueError(f"유효하지 않은 페이지 번호입니다: {page} (총 {len(doc)}페이지)")

        img_cv = _pdf_page_to_cv2(doc, page_num, dpi=dpi)
        success, png_data = cv2.imencode(".png", img_cv)
        if not success:
            raise RuntimeError("PNG 인코딩에 실패했습니다.")
        return png_data.tobytes()
    finally:
        doc.close()


def manual_crop_images(exam_key: int, pdf_key: int, crops: list[dict]) -> list[dict]:
    """
    사용자가 지정한 좌표로 PDF에서 이미지를 crop하여 R2에 업로드한다.
    좌표는 300dpi 기준이다.

    Args:
        exam_key: 시험 PK
        pdf_key: PDF 파일 PK
        crops: [{ "page": 1, "x": 100, "y": 200, "w": 300, "h": 400, "filename": "qst_5_1.png" }]
               page는 1-based, x/y/w/h는 300dpi 기준 픽셀

    Returns:
        생성된 이미지 정보 리스트 [{ "filename": "...", "r2_key": "..." }]
    """
    file_info = _get_pdf_file_info(exam_key, pdf_key)
    r2_key = file_info["file_path"]
    pdf_bytes = r2_storage.download_bytes(r2_key)
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    results = []
    try:
        # 페이지별로 그룹핑하여 같은 페이지는 한 번만 렌더링
        page_cache = {}
        for crop in crops:
            page_num = crop["page"] - 1  # 1-based → 0-based
            if page_num not in page_cache:
                page_cache[page_num] = _pdf_page_to_cv2(doc, page_num, dpi=300)

            img_cv = page_cache[page_num]
            x, y, w, h = crop["x"], crop["y"], crop["w"], crop["h"]

            # 이미지 경계 검증
            img_h, img_w = img_cv.shape[:2]
            x = max(0, min(x, img_w))
            y = max(0, min(y, img_h))
            w = min(w, img_w - x)
            h = min(h, img_h - y)

            if w <= 0 or h <= 0:
                continue

            cropped = img_cv[y:y + h, x:x + w]
            success, png_data = cv2.imencode(".png", cropped)
            if not success:
                continue

            filename = crop["filename"]
            r2_img_key = _r2_image_key(exam_key, filename)
            r2_storage.upload_bytes(r2_img_key, png_data.tobytes(), "image/png")

            results.append({
                "filename": filename,
                "r2_key": r2_img_key,
            })
    finally:
        doc.close()

    return results
