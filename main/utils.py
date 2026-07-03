import fitz
import os
import re
from django.conf import settings

try:
    from rapidfuzz import fuzz, process
except ImportError:
    fuzz = None
    process = None

class PDFSearchEngine:
    def __init__(self):
        self.cache = {}
    
    def extract_text_from_pdf(self, p):
        if not os.path.exists(p):
            return ""
        if p in self.cache:
            return self.cache[p]
        try:
            doc = fitz.open(p)
            n = doc.page_count
            txt = []
            for i in range(n):
                txt.append(f"[PG:{i+1}] {doc[i].get_text()}")
            doc.close()
            res = " ".join(txt)
            self.cache[p] = res
            return res
        except Exception:
            return ""

    def search_in_extracted_text(self, text, query):
        if not text:
            return {"found": False, "matches": [], "context": ""}
        matches = []
        all_context = []
        ql = query.lower()
        tl = text.lower()
        qp = re.escape(ql)
        marker_p = r"\[PG:(\d+)\]"
        for match in re.finditer(qp, tl):
            sp = match.start()
            ep = match.end()
            pre = text[:sp]
            markers = list(re.finditer(marker_p, pre))
            page = markers[-1].group(1) if markers else "N/A"
            cs = max(0, sp-80)
            ce = min(len(text), ep+80)
            raw_ctx = text[cs:ce]
            ctx = re.sub(marker_p, "", raw_ctx)
            m_in_ctx = ctx.lower().find(ql)
            h_ctx = self._h(ctx, query, 0, m_in_ctx)
            matches.append({"page": page, "position": sp, "context": h_ctx, "match_text": text[sp:ep]})
            all_context.append(h_ctx)
        return {
            "found": len(matches) > 0,
            "matches": matches[:10],
            "context": " ... ".join(all_context[:3]),
            "total_matches": len(matches)
        }

    def search_in_pdf(self, p, query):
        if not os.path.exists(p):
            return {"found": False, "matches": [], "context": ""}
        try:
            doc = fitz.open(p)
            matches = []
            all_ctx = []
            ql = query.lower()
            qp = re.escape(ql)
            for i in range(doc.page_count):
                page = doc[i]
                text = page.get_text()
                tl = text.lower()
                for m in re.finditer(qp, tl):
                    sp = m.start()
                    ep = m.end()
                    cs = max(0, sp-50)
                    ce = min(len(text), ep+50)
                    ctx = text[cs:ce]
                    h_ctx = self._h(ctx, query, cs, sp)
                    matches.append({"page": i+1, "position": sp, "context": h_ctx, "match_text": text[sp:ep]})
                    all_ctx.append(h_ctx)
            doc.close()
            return {"found": len(matches)>0, "matches": matches, "context": " ... ".join(all_ctx[:3]), "total_matches": len(matches)}
        except Exception:
            return {"found": False}

    def _h(self, ctx, q, cs, ms):
        from django.utils.html import escape
        mp = ms - cs
        ql = q.lower()
        mi = ctx.lower().find(ql, mp)
        if mi != -1:
            res = escape(ctx[:mi]) + f"<mark>{escape(ctx[mi:mi+len(q)])}</mark>" + escape(ctx[mi+len(q):])
            return res
        return escape(ctx)

    def get_pdf_preview(self, p, max_p=3):
        if not os.path.exists(p):
            return ""
        try:
            doc = fitz.open(p)
            txt = ""
            for i in range(min(max_p, doc.page_count)):
                txt += doc[i].get_text() + "\n\n"
            doc.close()
            return txt[:1000]
        except Exception:
            return ""

pdf_search_engine = PDFSearchEngine()

def search_in_thesis_pdf(t, q):
    if not t.file:
        return {"found": False}
    try:
        p = t.file.path
    except Exception:
        p = os.path.join(settings.MEDIA_ROOT, t.file.name)
    return pdf_search_engine.search_in_pdf(p, q)

def extract_thesis_text(t):
    if not t.file:
        return ""
    try:
        p = t.file.path
    except Exception:
        p = os.path.join(settings.MEDIA_ROOT, t.file.name)
    return pdf_search_engine.extract_text_from_pdf(p)

def get_thesis_preview(t, max_p=3):
    if not t.file:
        return ""
    try:
        p = t.file.path
    except Exception:
        p = os.path.join(settings.MEDIA_ROOT, t.file.name)
    return pdf_search_engine.get_pdf_preview(p, max_p)

def extract_abstract_from_pdf(f):
    try:
        import pdfplumber
        import tempfile
        if hasattr(f, "read"):
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                for c in f.chunks():
                    tmp.write(c)
                p = tmp.name
                sd = True
        else:
            p = f
            sd = False
        if not os.path.exists(p):
            return ""
        txt = ""
        with pdfplumber.open(p) as pdf:
            for pg in pdf.pages[:8]:
                t = pg.extract_text(layout=True)
                if not t:
                    continue
                ls = t.split("\n")
                for idx, line in enumerate(ls):
                    if re.search(r"(?i)^\s*(abstract|summary|executive summary)\s*$", line.strip()) or re.search(r"(?i)abstract[:\-\s]", line.strip()):
                        s_idx = idx + 1 if len(ls[idx].strip()) < 15 else idx
                        txt = " ".join([li.strip() for li in ls[s_idx:] if li.strip()])
                        break
                if txt:
                    break
        if not txt:
            with pdfplumber.open(p) as pdf:
                for pg in pdf.pages[1:4]:
                    ps = [pa.strip() for pa in re.split(r"\n\s*\n", pg.extract_text() or "") if len(pa.split()) > 50]
                    if ps:
                        txt = ps[0]
                        break
        if sd:
            os.unlink(p)
        res = re.sub(r"\s+", " ", txt).strip()[:1000]
        return res
    except Exception:
        return ""

def extract_title_from_pdf(f):
    try:
        if hasattr(f, "read"):
            import tempfile
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                for c in f.chunks():
                    tmp.write(c)
                p = tmp.name
                sd = True
        else:
            p = f
            sd = False
        doc = fitz.open(p)
        title = ""
        if doc.page_count > 0:
            blocks = doc[0].get_text("dict").get("blocks", [])
            lines = [line_item for b in blocks if "lines" in b for line_item in b["lines"]]
            best_c = None
            best_s = 0
            for line in lines:
                spans = line.get("spans", [])
                text = " ".join([s["text"] for s in spans]).strip()
                if 10 < len(text) < 300:
                    sz = spans[0].get("size", 0)
                    is_b = bool(spans[0].get("flags", 0) & 16)
                    score = sz * (2 if is_b else 1)
                    if score > best_s:
                        best_s = score
                        best_c = text
            title = best_c or ""
        doc.close()
        if sd:
            os.unlink(p)
        return title
    except Exception:
        return ""

def suggest_query_correction(q, cs):
    if not q or not cs:
        return (None, 0.0)
    qn = q.strip().lower()
    qt = [t.lower() for t in re.findall(r"\w+", q) if t.strip()]
    if not qt:
        return (None, 0.0)
    AMAP = {"cct": "cict", "cict": "cict", "cas": "cas", "cba": "cbah", "coe": "coe", "chm": "chm", "ced": "ced", "tcu": "tcu", "lib": "library", "ippg": "ippg"}
    if qn in AMAP:
        return (AMAP[qn], 1.0)
    try:
        from main.nlp_utils import get_english_dictionary_words, get_lemmas
        dw = get_english_dictionary_words()
    except Exception:
        dw = set()
        def get_lemmas(w):
            return {w.lower()}
    wc = set()
    for c in cs:
        for w in re.findall(r"\w+", c.lower()):
            wc.add(w)
    for w in dw:
        wc.add(w.lower())
    wl = list(wc)
    known = (qn in [c.lower() for c in cs])
    if not known:
        wf = True
        for t in qt:
            if t in wc or any(lemma in wc for lemma in get_lemmas(t)):
                continue
            wf = False
            break
        known = wf
    if known:
        return (None, 0.0)
    st = []
    ts = []
    for t in qt:
        if t in wc or any(lemma in wc for lemma in get_lemmas(t)):
            st.append(t)
            ts.append(100.0)
            continue
        if process:
            m = process.extractOne(t, wl, scorer=fuzz.ratio, score_cutoff=75)
            if m:
                st.append(m[0])
                ts.append(float(m[1]))
            else:
                st.append(t)
                ts.append(100.0)
        else:
            st.append(t)
            ts.append(100.0)
    tj = " ".join(st).strip()
    tc = (sum(ts) / len(ts) / 100.0) if ts else 0.0
    if len(qt) > 1 and tc < 0.9 and process:
        pm = process.extractOne(qn, cs, scorer=fuzz.token_sort_ratio, score_cutoff=85)
        if pm and abs(len(pm[0].split()) - len(qt)) <= 2:
            return (pm[0], float(pm[1]) / 100.0)
    if tj.lower() != qn and tc > 0.75:
        return (tj, tc)
    return (None, 0.0)

def deep_filter_theses_by_pdf(tlist, q):
    if not q:
        return []
    matched = []
    for t in tlist:
        if not getattr(t, "file", None):
            continue
        res = search_in_thesis_pdf(t, q)
        if res.get("found"):
            t.deep_search_results = res
            t.deep_search_query = q
            t.match_count = res.get("total_matches", 1)
            matched.append(t)
    matched.sort(key=lambda x: x.match_count, reverse=True)
    return matched
