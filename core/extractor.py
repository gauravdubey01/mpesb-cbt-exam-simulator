import os
import re
import sys
import json
import pymupdf

def is_devanagari(char):
    return '\u0900' <= char <= '\u097f'

def has_devanagari(text):
    return any(is_devanagari(c) for c in text)

def has_latin(text):
    return any('A' <= c <= 'Z' or 'a' <= c <= 'z' for c in text)

def split_bilingual_lines(lines):
    """
    Separates a list of lines into English lines and Hindi lines.
    """
    en_lines = []
    hi_lines = []
    for l in lines:
        clean = l.strip().replace('\xa0', ' ')
        if not clean:
            continue
        h_dev = has_devanagari(clean)
        h_lat = has_latin(clean)
        if h_dev and not h_lat:
            hi_lines.append(clean)
        elif h_lat and not h_dev:
            en_lines.append(clean)
        elif h_dev and h_lat:
            hi_lines.append(clean)
            en_lines.append(clean)
        else:
            en_lines.append(clean)
            hi_lines.append(clean)
    
    en_text = '\n'.join(en_lines).strip()
    hi_text = '\n'.join(hi_lines).strip()
    return en_text, hi_text

class PDFExtractor:
    def __init__(self, pdf_path="G2SG4_Patwari_2022_QB.pdf", cache_dir="cache"):
        self.pdf_path = os.path.abspath(pdf_path)
        self.cache_dir = os.path.abspath(cache_dir)
        self.img_cache_dir = os.path.join(self.cache_dir, "img_cache")
        os.makedirs(self.img_cache_dir, exist_ok=True)
        self._doc = None

    def get_doc(self):
        if self._doc is None or self._doc.is_closed:
            self._doc = pymupdf.open(self.pdf_path)
        return self._doc

    def close(self):
        if self._doc and not self._doc.is_closed:
            self._doc.close()
            self._doc = None

    def scan_shifts(self):
        """Scans the PDF to find all 70 test shifts."""
        doc = self.get_doc()
        shifts = []
        for p in range(len(doc)):
            text = doc[p].get_text("text")
            if "Testdate" in text and "TestSlot" in text:
                dt_m = re.search(r"Testdate\s*\n\s*([^\n]+)", text)
                slot_m = re.search(r"TestSlot\s*\n\s*([^\n]+)", text)
                dt = dt_m.group(1).strip() if dt_m else "Unknown"
                slot = slot_m.group(1).strip() if slot_m else "Unknown"
                shifts.append({
                    "shift_index": len(shifts) + 1,
                    "start_page": p,
                    "date": dt,
                    "slot": slot
                })
        for i in range(len(shifts)):
            if i < len(shifts) - 1:
                shifts[i]["end_page"] = shifts[i + 1]["start_page"] - 1
            else:
                shifts[i]["end_page"] = len(doc) - 1
            shifts[i]["page_count"] = shifts[i]["end_page"] - shifts[i]["start_page"] + 1
            shifts[i]["name"] = f"Test #{shifts[i]['shift_index']:02d} - {shifts[i]['date']} ({shifts[i]['slot']})"
        return shifts

    def parse_shift_questions(self, shift_info):
        """
        Parses all questions in a given shift (pages start_page to end_page).
        Returns a list of dicts with question details and extracted images.
        """
        doc = self.get_doc()
        start_page = shift_info["start_page"]
        end_page = shift_info["end_page"]
        shift_idx = shift_info["shift_index"]

        page_texts = []
        page_q_starts = {}
        for p in range(start_page, end_page + 1):
            txt = doc[p].get_text("text")
            page_texts.append((p, txt))
            for qm in re.finditer(r"Q\.No:\s*(\d+)", txt):
                qno = int(qm.group(1))
                if qno not in page_q_starts:
                    page_q_starts[qno] = p

        full_shift_text = "\n".join([pt[1] for pt in page_texts])
        parts = re.split(r"Q\.No:\s*(\d+)", full_shift_text)

        questions = []
        for i in range(1, len(parts), 2):
            qno = int(parts[i])
            raw_block = parts[i + 1].strip()

            q_data = self._parse_single_question_block(qno, raw_block)
            q_page = page_q_starts.get(qno, start_page)
            q_data["shift_id"] = shift_idx
            q_data["page_num"] = q_page

            img_paths = self._extract_question_images(shift_idx, qno, q_page)
            q_data["images"] = img_paths

            questions.append(q_data)

        return questions

    def _parse_single_question_block(self, qno, raw):
        raw = raw.replace('\xa0', ' ')
        subj_m = re.search(r"Subject\s*:\s*(.+?)(?:\n|$)", raw)
        ans_m = re.search(r"Correct Ans\s*:\s*([A-D]|Cancelled|Bonus|[^\n]+)", raw)

        subject = subj_m.group(1).strip() if subj_m else "General"
        correct_ans = ans_m.group(1).strip() if ans_m else "N/A"
        if len(correct_ans) > 1 and correct_ans[0] in ('A', 'B', 'C', 'D'):
            correct_ans = correct_ans[0]

        body = re.sub(r"Correct Ans\s*:\s*.*", "", raw, flags=re.DOTALL).strip()
        lines = [l.strip() for l in body.splitlines() if l.strip()]

        qid = ""
        if lines and lines[0].isdigit():
            qid = lines[0]
            lines = lines[1:]

        opt_indices = {"A": -1, "B": -1, "C": -1, "D": -1}
        for idx, line in enumerate(lines):
            l_strip = line.strip()
            if l_strip == "A" and opt_indices["A"] == -1:
                opt_indices["A"] = idx
            elif l_strip == "B" and opt_indices["A"] != -1 and opt_indices["B"] == -1:
                opt_indices["B"] = idx
            elif l_strip == "C" and opt_indices["B"] != -1 and opt_indices["C"] == -1:
                opt_indices["C"] = idx
            elif l_strip == "D" and opt_indices["C"] != -1 and opt_indices["D"] == -1:
                opt_indices["D"] = idx

        options_raw = {"A": [], "B": [], "C": [], "D": []}
        q_lines = []

        if all(v != -1 for v in opt_indices.values()):
            q_lines = lines[:opt_indices["A"]]
            options_raw["A"] = lines[opt_indices["A"] + 1 : opt_indices["B"]]
            options_raw["B"] = lines[opt_indices["B"] + 1 : opt_indices["C"]]
            options_raw["C"] = lines[opt_indices["C"] + 1 : opt_indices["D"]]
            options_raw["D"] = lines[opt_indices["D"] + 1 :]
        else:
            q_lines = lines

        q_en, q_hi = split_bilingual_lines(q_lines)
        if not q_hi and q_en and has_devanagari(q_en):
            q_hi = q_en
        if not q_en and q_hi and not has_devanagari(q_hi):
            q_en = q_hi

        opt_data = {}
        for key in ("A", "B", "C", "D"):
            en, hi = split_bilingual_lines(options_raw[key])
            if not hi and en and has_devanagari(en):
                hi = en
            if not en and hi and not has_devanagari(hi):
                en = hi
            opt_data[key] = {
                "en": en if en else ('\n'.join(options_raw[key]) if not hi else ''),
                "hi": hi if hi else ('\n'.join(options_raw[key]) if not en else ''),
                "full": '\n'.join(options_raw[key])
            }

        return {
            "qno": qno,
            "qid": qid,
            "subject": subject,
            "question_en": q_en,
            "question_hi": q_hi,
            "question_full": '\n'.join(q_lines),
            "opt_a_en": opt_data["A"]["en"],
            "opt_a_hi": opt_data["A"]["hi"],
            "opt_a_full": opt_data["A"]["full"],
            "opt_b_en": opt_data["B"]["en"],
            "opt_b_hi": opt_data["B"]["hi"],
            "opt_b_full": opt_data["B"]["full"],
            "opt_c_en": opt_data["C"]["en"],
            "opt_c_hi": opt_data["C"]["hi"],
            "opt_c_full": opt_data["C"]["full"],
            "opt_d_en": opt_data["D"]["en"],
            "opt_d_hi": opt_data["D"]["hi"],
            "opt_d_full": opt_data["D"]["full"],
            "correct_ans": correct_ans
        }

    def _extract_question_images(self, shift_idx, qno, page_idx):
        saved_paths = []
        doc = self.get_doc()
        if page_idx >= len(doc):
            return saved_paths

        pages_to_check = [page_idx]
        if page_idx + 1 < len(doc):
            pages_to_check.append(page_idx + 1)

        for p in pages_to_check:
            page = doc[p]
            q_search = page.search_for(f"Q.No: {qno}") or page.search_for(f"Q.No:\xa0{qno}")
            if not q_search and p != page_idx:
                continue

            q_top = q_search[0].y0 if q_search else 0.0
            next_q = page.search_for(f"Q.No: {qno + 1}") or page.search_for(f"Q.No:\xa0{qno + 1}")
            q_bottom = next_q[0].y0 if next_q else page.rect.height

            for img_info in page.get_image_info(xrefs=True):
                xref = img_info.get("xref", 0)
                if not xref:
                    continue
                bbox = img_info.get("bbox")
                if not bbox:
                    continue
                
                if bbox[3] >= q_top and bbox[1] <= q_bottom:
                    w = img_info.get("width", 0)
                    h = img_info.get("height", 0)
                    if w > 30 and h > 20 and (w * h > 1200):
                        filename = f"s{shift_idx}_q{qno}_x{xref}.png"
                        out_path = os.path.join(self.img_cache_dir, filename)
                        if not os.path.exists(out_path):
                            try:
                                base_img = doc.extract_image(xref)
                                if base_img and "image" in base_img:
                                    with open(out_path, "wb") as f:
                                        f.write(base_img["image"])
                            except Exception:
                                pass
                        if os.path.exists(out_path) and out_path not in saved_paths:
                            saved_paths.append(out_path)

        return saved_paths

    def render_question_clip(self, shift_idx, qno, page_idx, dpi=150):
        doc = self.get_doc()
        if page_idx >= len(doc):
            return None

        page = doc[page_idx]
        q_search = page.search_for(f"Q.No: {qno}") or page.search_for(f"Q.No:\xa0{qno}")
        if not q_search:
            return None

        q_top = max(0, q_search[0].y0 - 5)
        next_q = page.search_for(f"Q.No: {qno + 1}") or page.search_for(f"Q.No:\xa0{qno + 1}")
        if next_q:
            q_bottom = min(page.rect.height, next_q[0].y0 - 5)
        else:
            sub_search = page.search_for("Subject :")
            if sub_search:
                last_sub = sub_search[-1]
                q_bottom = min(page.rect.height, last_sub.y1 + 10)
            else:
                q_bottom = page.rect.height

        clip_rect = pymupdf.Rect(0, q_top, page.rect.width, q_bottom)
        clip_filename = f"clip_s{shift_idx}_q{qno}.png"
        clip_path = os.path.join(self.img_cache_dir, clip_filename)

        if not os.path.exists(clip_path):
            mat = pymupdf.Matrix(dpi / 72, dpi / 72)
            pix = page.get_pixmap(matrix=mat, clip=clip_rect)
            pix.save(clip_path)

        return clip_path
