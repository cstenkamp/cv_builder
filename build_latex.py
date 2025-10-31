from cv_builder import CVBuilder
import re, json, argparse, pathlib
from typing import Any, Dict, List

# vibecoded: https://chatgpt.com/c/6904986d-3468-8321-8cb8-30073fe1e723

def main(path):
    cv = CVBuilder(path).build_variant(language="de", annotate_kind=False)
    template_path = "/home/chris/Documents/projects/cstenkamp.de/components/cv_builder/static/cv_template.tex"
    out = "/home/chris/Documents/projects/cstenkamp.de/components/cv/cv_generated.tex"
    site_base = "https://cstenkamp.de"
    template = pathlib.Path(template_path).read_text(encoding="utf-8")
    tex = CV2LaTeX(cv, template, site_base=site_base.removeprefix("https://"), include_closing=True).render()
    pathlib.Path(out).write_text(tex, encoding="utf-8")


# def main():
#     ap = argparse.ArgumentParser()
#     ap.add_argument("--in", required=True)
#     ap.add_argument("--template", required=True)
#     ap.add_argument("--out", required=True)
#     ap.add_argument("--site", default="cstenkamp.de")
#     ap.add_argument("--closing", action="store_true")
#     ap.add_argument("--ae", action="store_true")  # switch title to "Curriculum Vitae"
#     ap.add_argument("--style", default="casual", choices=["casual", "classic", "modern"])
#     ap.add_argument("--social", action="store_true")
#     args = ap.parse_args()
#     data = load_data(data_path) if isinstance(data_path, str) and pathlib.Path(data_path).suffix else data_path
#     template = pathlib.Path(template_path).read_text(encoding="utf-8")
#     tex = CV2LaTeX(data, template, site_base=site_base, include_closing=include_closing).render()
#     pathlib.Path(out_path).write_text(tex, encoding="utf-8")

class CV2LaTeX:
    def __init__(self, data: Dict[str, Any], template_text: str, site_base: str = "cstenkamp.de",
                 include_closing: bool = False, lang: str = "de", ae_title: bool = False,
                 cv_style: str = "casual", strip_comments: bool = True, include_social: bool = False):
        self.data = data
        self.tpl = self._apply_style(template_text, cv_style)
        self.site_base = site_base.strip().rstrip("/")
        self.include_closing = include_closing
        self.lang = (lang or "de").lower()
        self.ae_title = bool(ae_title)
        self.strip_comments = strip_comments
        self.include_social = include_social

    # ---------------------------- public ----------------------------

    def render(self) -> str:
        basic = self._basic_info(self.data.get("Basic Info", {})).strip()
        sections = self._render_sections({k: v for k, v in self.data.items() if k != "Basic Info"}).rstrip()
        if self.include_closing:
            sections += self._closing_block()
        out = self._sub_anchor(self.tpl, "BASIC_INFO", basic)
        out = self._sub_anchor(out, "SECTIONS", sections)
        return self._strip_comment_lines(out) if self.strip_comments else out

    # ---------------------------- template ops ----------------------------

    def _apply_style(self, tpl: str, style: str) -> str:
        return re.sub(r"(\\moderncvstyle\{)[^}]+(\})", r"\1%s\2" % style, tpl, count=1)

    def _sub_anchor(self, txt: str, name: str, payload: str) -> str:
        pat = re.compile(r"^[ \t]*%%" + name + r"%%[ \t]*$", re.MULTILINE)
        return pat.sub(lambda m: payload, txt, count=1)

    def _strip_comment_lines(self, s: str) -> str:
        return re.sub(r"(?m)^[ \t]*%.*\n?", "", s)

    # ---------------------------- header ----------------------------

    def _basic_info(self, info: Dict[str, Any]) -> str:
        def img_name(s: str) -> str:
            m = re.match(r"\s*img\(([^)]+)\)\s*$", str(s or ""))
            return m.group(1) if m else str(s or "")

        kv = {k.lower(): v for k, v in info.items()}
        lines: List[str] = []

        firstname = kv.get("firstname", "")
        familyname = kv.get("familyname", "")
        title_val = "Curriculum Vitae" if self.ae_title else kv.get("title", "Lebenslauf")

        if firstname: lines.append("\\firstname{%s}" % self._esc(firstname))
        if familyname: lines.append("\\familyname{%s}" % self._esc(familyname))
        lines.append("\\title{%s}" % self._esc(title_val))

        addr = kv.get("address_hidden")
        if isinstance(addr, list) and len(addr) >= 2:
            lines.append("\\address{%s}{%s}" % (self._esc(addr[0]), self._esc(addr[1])))

        if kv.get("mobile"): lines.append("\\mobile{%s}" % self._esc(kv["mobile"]))
        if kv.get("email"): lines.append("\\email{%s}" % self._esc(kv["email"]))
        if kv.get("homepage"): lines.append("\\homepage{%s}" % self._esc(self._homepage_text(kv["homepage"])))
        if kv.get("photo"):
            fn = img_name(kv["photo"])
            if fn: lines.append("\\photo[85pt][0pt]{%s}" % fn)

        extras = []
        if kv.get("github_user"):  extras.append("\\githubsocial{%s}" % self._esc(kv["github_user"]))
        if kv.get("linkedin_user"): extras.append("\\linkedinsocial{%s}" % self._esc(kv["linkedin_user"]))
        if kv.get("so_user"):      extras.append("\\social[stackoverflow]{%s}" % self._esc(kv["so_user"]))
        if extras:
            if self.include_social:
                lines.append(" ".join(extras))  # visible line
            else:
                lines.append("% " + " ".join(extras))  # commented, will be stripped

        # exact blank-line/indent style
        return "\n".join(lines) + "\n"

    def _homepage_text(self, s: Any) -> str:
        t = str(s or "").strip()
        m = re.match(r"^\[([^\]]+)\]\(([^)]+)\)$", t)
        if m: return m.group(1)
        return re.sub(r"^https?://", "", t)

    # ---------------------------- sections ----------------------------

    def _render_sections(self, sections: Dict[str, Any]) -> str:
        chunks: List[str] = []
        for raw_name, content in sections.items():
            sec_name = self._section_label(raw_name)
            sec_head = "\\section{%s}" % self._esc(sec_name)
            body = self._render_section_body(sec_name, content)
            chunks.append("\n\n" + sec_head + "\n\n" + body)
        return "".join(chunks) + "\n"

    def _section_label(self, name: str) -> str:
        de = {
            "personal information": "Pers\u00f6nliche Information",
            "bildungsweg": "Ausbildung",
            "education": "Ausbildung",
            "berufserfahrung": "Berufserfahrung",
            "programming languages and computer skills": "Programmiersprachen und -kompetenzen",
            "nat\u00fcrliche sprachen": "Nat\u00fcrliche Sprachen",
            "ehrenamt und akademische selbstverwaltung": "Ehrenamt und akademische Selbstverwaltung",
        }
        en = {
            "personal information": "Personal Information",
            "education": "Education",
            "work experience": "Work Experience",
            "programming languages and computer skills": "Programming Languages and Computer Skills",
            "languages": "Languages",
            "volunteering and academic self-governance": "Volunteering and Academic Service",
        }
        key = name.strip().lower()
        if self.lang.startswith("en"):
            return en.get(key, name)
        return de.get(key, name)

    def _render_section_body(self, sec_name: str, content: Any) -> str:
        if isinstance(content, list) and content and isinstance(content[0], dict):
            return self._render_entries(sec_name, content)
        if isinstance(content, list):
            return self._render_list_section(content)
        if isinstance(content, dict):
            return self._render_kv_section(sec_name, content)
        if content:
            return "    \\cvitem{}{%s}" % self._fmt_text(str(content))
        return ""

    def _render_entries(self, sec_name: str, entries: List[Dict[str, Any]]) -> str:
        lines = []
        for e in entries:
            lines.append("\t" + self._cventry(sec_name, e))
        return "\n\n".join(lines) + "\n"

    def _cventry(self, sec_name: str, e: Dict[str, Any]) -> str:
        time = self._normalize_time(self._fmt_text(e.get("time", "")))
        title = self._fmt_text(e.get("title", ""))
        employer = self._fmt_text(e.get("employer", ""))
        place = self._fmt_text(e.get("place", ""))

        # link title via hp_link (site_base applied)
        hp = e.get("hp_link") or ""
        if hp:
            title = self._link_text(title, self._abs_url(hp))

        # 5th arg: Note (edu) else website (italic)
        opt5 = ""
        if self._is_edu_section(sec_name) and e.get("optshort"):
            opt5 = self._fmt_text(e.get("optshort"))
        else:
            website = e.get("website") or ""
            if website:
                opt5 = "\\textit{%s}" % self._urlify(website)

        body = self._fmt_text(e.get("optlong") or "")
        return "\\cventry{%s}{%s}{%s}{%s}{%s}{%s}" % (time, title, employer, place, opt5, body)

    def _render_list_section(self, items: List[Any]) -> str:
        if not items: return ""
        for i, it in enumerate(items):
            if isinstance(it, str) and re.search(r"design\s*:\s*paragraphs", it, re.I):
                payload = items[i+1:]
                return "\n".join("    \\cvitem{}{%s}" % self._fmt_text(str(x)) for x in payload)
        return "\\begin{itemize}\n%s\n\\end{itemize}" % "\n".join("\t\\item %s" % self._fmt_text(str(x)) for x in items)

    def _render_kv_section(self, sec_name: str, d: Dict[str, Any]) -> str:
        rows = []
        use_withcomment = sec_name.lower().startswith("nat") or "design" in d
        for k, v in d.items():
            if k == "design": continue
            if use_withcomment and isinstance(v, list):
                if len(v) >= 2:
                    rows.append("    \\cvitemwithcomment{%s}{%s}{%s}" % (self._esc(k), self._fmt_text(v[0]), self._fmt_text(v[1])))
                elif len(v) == 1:
                    rows.append("    \\cvitem{%s}{%s}" % (self._esc(k), self._fmt_text(v[0])))
                else:
                    rows.append("    \\cvitem{%s}{}" % self._esc(k))
            else:
                rows.append("    \\cvitem{%s}{%s}" % (self._esc(k), self._fmt_text(v)))
        return "\n".join(rows)

    # ---------------------------- helpers ----------------------------

    def _is_edu_section(self, sec_name: str) -> bool:
        s = sec_name.strip().lower()
        return ("bildung" in s) or ("ausbildung" in s) or ("education" in s)

    def _normalize_time(self, s: str) -> str:
        if self.lang.startswith("en"): return s.replace("aktuell", "present")
        return s.replace("today", "aktuell").replace("present", "aktuell")

    def _abs_url(self, url: str) -> str:
        t = str(url or "").strip()
        if t.startswith("http://") or t.startswith("https://"): return t
        if not t.startswith("/"): t = "/" + t
        return "https://" + self.site_base + t

    def _link_text(self, label: str, url: str) -> str:
        return "\\httplink[%s]{%s}" % (self._esc(label), self._esc_url(url))

    def _esc_url(self, s: Any) -> str:
        t = str(s or "")
        return t.replace("%", r"\%").replace("#", r"\#").replace(" ", "%20").rstrip("/")

    def _urlify(self, s: Any) -> str:
        t = str(s or "").strip()
        if not t: return ""
        if "\\httplink" in t: return t
        m = re.match(r"^\[([^\]]+)\]\(([^)]+)\)$", t)
        if m: return "\\httplink[%s]{%s}" % (self._esc(m.group(1)), self._esc_url(self._abs_url(m.group(2))))
        if t.startswith("http") or t.startswith("/"): return "\\httplink{%s}" % self._esc_url(self._abs_url(t))
        return self._esc(t)

    def _md_to_href(self, s: str) -> str:
        def repl(m):
            txt = m.group(1)
            url = self._abs_url(m.group(2))
            return "\\httplink[%s]{%s}" % (txt, self._esc_url(url))
        return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl, s or "")

    def _format_emphasis(self, t: str) -> str:
        t = re.sub(r"\*\*([^\*\n]+)\*\*", lambda m: r"\bo{" + m.group(1) + "}", t)
        t = re.sub(r"\*([^\*\n]+)\*", lambda m: r"\textit{" + m.group(1) + "}", t)
        return t

    def _smart_quotes(self, t: str) -> str:
        out = []
        openq = True
        i = 0
        while i < len(t):
            c = t[i]
            if c == '"' and (i == 0 or t[i-1] != "\\"):
                out.append("``" if openq else "''")
                openq = not openq
            else:
                out.append(c)
            i += 1
        return "".join(out)

    def _fmt_text(self, s: Any) -> str:
        t = str(s or "")
        t = self._md_to_href(t)
        t = self._format_emphasis(t)
        t = self._smart_quotes(t)
        t = (t.replace("•", r"\textbullet{}")
             .replace("<br>", " \\\\ ")
             .replace("<br/>", " \\\\ ")
             .replace("<br />", " \\\\ "))
        return self._esc(t)

    def _esc(self, s: Any) -> str:
        t = str(s or "")
        if "\\" in t:  # allow LaTeX macros to pass
            return t
        t = re.sub(r"([%&#_$\{\}])", r"\\\1", t)
        t = t.replace("^", "\\textasciicircum{}").replace("~", "\\textasciitilde{}")
        return t

    def _closing_block(self) -> str:
        return ("\n\\vfill\n"
                "\\closing{K\\\"oln, \\today\n"
                "\\newline\n"
                "\\includegraphics[height=30pt]{signature}\n"
                "\\vspace{-30pt}\n"
                "}\n"
                "\\makeletterclosing\n")



def load_data(path: str) -> Dict[str, Any]:
    p = pathlib.Path(path)
    txt = p.read_text(encoding="utf-8")
    if p.suffix.lower() in (".yaml", ".yml"):
        import yaml  # pip install pyyaml
        return yaml.safe_load(txt)
    if p.suffix.lower() == ".json":
        return json.loads(txt)
    raise ValueError("Provide .yaml/.yml or .json")


if __name__ == "__main__":
    from os.path import dirname, join
    main(join(dirname(__file__), "..", "cv", "all_cvs.yaml"))