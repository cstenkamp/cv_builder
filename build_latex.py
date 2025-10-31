from cv_builder import CVBuilder
import re, json, argparse, pathlib
from typing import Any, Dict, List

# vibecoded: https://chatgpt.com/c/6904986d-3468-8321-8cb8-30073fe1e723

def main(path):
    cv = CVBuilder(path).build_variant(language="de", annotate_kind=False)
    template_path = "/home/chris/Documents/projects/cstenkamp.de/components/cv_builder/static/cv_template.tex"
    out = "/home/chris/Documents/projects/cstenkamp.de/components/cv/cv_generated.tex"
    template = pathlib.Path(template_path).read_text(encoding="utf-8")
    tex = CV2LaTeX(cv, template).render()
    pathlib.Path(out).write_text(tex, encoding="utf-8")


# def main():
#     ap = argparse.ArgumentParser()
#     ap.add_argument("--in", dest="inp", required=True)
#     ap.add_argument("--template", dest="tpl", required=True)
#     ap.add_argument("--out", dest="out", required=True)
#     args = ap.parse_args()
#     data = load_data(args.inp)
#     template = pathlib.Path(args.tpl).read_text(encoding="utf-8")
#     tex = CV2LaTeX(data, template).render()
#     pathlib.Path(args.out).write_text(tex, encoding="utf-8")


class CV2LaTeX:
    def __init__(self, data: Dict[str, Any], template_text: str):
        self.data = data
        self.tpl = template_text

    def render(self) -> str:
        basic = self._basic_info(self.data.get("Basic Info", {})).strip()
        sections = self._render_sections({k: v for k, v in self.data.items() if k != "Basic Info"}).strip()
        out = self._sub_anchor(self.tpl, "BASIC_INFO", basic)
        out = self._sub_anchor(out, "SECTIONS", sections)
        return out

    def _homepage_text(self, s: Any) -> str:
        t = str(s or "").strip()
        m = re.match(r"^\[([^\]]+)\]\(([^)]+)\)$", t)
        if m:
            return m.group(1)
        # strip scheme to keep header clean
        t = re.sub(r"^https?://", "", t)
        return t

    def _sub_anchor(self, txt: str, name: str, payload: str) -> str:
        pat = re.compile(r"^[ \t]*%%" + name + r"%%[ \t]*$", re.MULTILINE)
        if not pat.search(txt):
            raise ValueError(f"anchor %%{name}%% not found in template")
        return pat.sub(lambda m: payload, txt, count=1)

    def _basic_info(self, info: Dict[str, Any]) -> str:
        def img_name(s: str) -> str:
            m = re.match(r"\s*img\(([^)]+)\)\s*$", str(s or ""))
            return m.group(1) if m else str(s or "")
        lines = []
        kv = {k.lower(): v for k, v in info.items()}
        if "firstname" in kv: lines.append("\\firstname{%s}" % self._esc(kv["firstname"]))
        if "familyname" in kv: lines.append("\\familyname{%s}" % self._esc(kv["familyname"]))
        if "title" in kv: lines.append("\\title{%s}" % self._esc(kv["title"]))
        if "address_hidden" in kv:
            addr = kv["address_hidden"]
            if isinstance(addr, list) and len(addr) >= 2:
                lines.append("\\address{%s}{%s}" % (self._esc(addr[0]), self._esc(addr[1])))
        if "mobile" in kv: lines.append("\\mobile{%s}" % self._esc(kv["mobile"]))
        if "email" in kv: lines.append("\\email{%s}" % self._esc(kv["email"]))
        if "homepage" in kv:
            lines.append("\\homepage{%s}" % self._esc(self._homepage_text(kv["homepage"])))
        if "photo" in kv:
            fn = img_name(kv["photo"])
            if fn: lines.append("\\photo[85pt][0pt]{%s}" % fn)
        extras = []
        if "github_user" in kv: extras.append("\\githubsocial{%s}" % self._esc(kv["github_user"]))
        if "linkedin_user" in kv: extras.append("\\linkedinsocial{%s}" % self._esc(kv["linkedin_user"]))
        if "so_user" in kv: extras.append("\\social[stackoverflow]{%s}" % self._esc(kv["so_user"]))
        if extras: lines.append("% " + " ".join(extras))
        return "\n\t".join(lines) + "\n"

    def _render_sections(self, sections: Dict[str, Any]) -> str:
        out: List[str] = []
        for name, content in sections.items():
            out.append("\\section{%s}" % self._esc(name))
            if isinstance(content, list):
                if content and isinstance(content[0], dict):
                    out += [self._cventry(e) for e in content]
                else:
                    out.append(self._list_or_paragraphs(content))
            elif isinstance(content, dict):
                out.append(self._dict_section(name, content))
            elif content:
                out.append("\\cvitem{}{%s}" % self._fmt_text(str(content)))
        return "\n".join([x for x in out if x])

    def _cventry(self, e: Dict[str, Any]) -> str:
        time = self._fmt_text(e.get("time", ""))
        title = self._fmt_text(e.get("title", ""))
        employer = self._fmt_text(e.get("employer", ""))
        place = self._fmt_text(e.get("place", ""))
        link = e.get("website") or e.get("hp_link") or ""
        opt5 = "\\textit{%s}" % self._urlify(link) if link else ""
        body = e.get("optlong") or e.get("optshort") or ""
        return "\t\\cventry{%s}{%s}{%s}{%s}{%s}{%s}" % (
            time, title, employer, place, opt5, self._fmt_text(body)
        )

    def _list_or_paragraphs(self, items: List[Any]) -> str:
        if not items: return ""
        mode, drop_until = "", -1
        for i, it in enumerate(items):
            if isinstance(it, str) and re.search(r"design\s*:\s*paragraphs", it, re.I):
                mode, drop_until = "paragraphs", i
                break
        payload = items[drop_until + 1:] if mode else items
        if mode == "paragraphs":
            return "\n".join("\\cvitem{}{%s}" % self._fmt_text(str(x)) for x in payload)
        return "\\begin{itemize}\n%s\n\\end{itemize}" % "\n".join(
            "\t\\item %s" % self._fmt_text(str(x)) for x in payload
        )

    def _dict_section(self, name: str, d: Dict[str, Any]) -> str:
        if name.lower().startswith("nat") or "design" in d:
            rows = []
            for k, v in d.items():
                if k == "design": continue
                if isinstance(v, list):
                    if len(v) >= 2:
                        rows.append("\\cvitemwithcomment{%s}{%s}{%s}" % (
                            self._esc(k), self._fmt_text(v[0]), self._fmt_text(v[1])
                        ))
                    elif len(v) == 1:
                        rows.append("\\cvitem{%s}{%s}" % (self._esc(k), self._fmt_text(v[0])))
                    else:
                        rows.append("\\cvitem{%s}{}" % self._esc(k))
                else:
                    rows.append("\\cvitem{%s}{%s}" % (self._esc(k), self._fmt_text(v)))
            return "\n".join(rows)
        return "\n".join("\\cvitem{%s}{%s}" % (self._esc(k), self._fmt_text(v)) for k, v in d.items())

    def _esc_url(self, s: Any) -> str:
        t = str(s or "")
        # only escape things that break in moving args
        t = t.replace("%", r"\%").replace("#", r"\#").replace(" ", "%20")
        return t

    def _urlify(self, s: Any) -> str:
        t = str(s or "").strip()
        if not t: return ""
        if "\\httplink" in t: return t
        m = re.match(r"^\[([^\]]+)\]\(([^)]+)\)$", t)
        if m:
            txt = self._esc(m.group(1))
            url = self._esc_url(m.group(2))
            return "\\httplink[%s]{%s}" % (txt, url)
        if t.startswith("http") or t.startswith("/"):
            return "\\httplink{%s}" % self._esc_url(t)
        return self._esc(t)

    def _fmt_text(self, s: Any) -> str:
        t = str(s or "")
        t = self._md_to_href(t)
        t = (t.replace("•", r"\textbullet{}")
             .replace("<br>", " \\\\ ")
             .replace("<br/>", " \\\\ ")
             .replace("<br />", " \\\\ "))
        return self._esc(t)

    def _md_to_href(self, s: str) -> str:
        def repl(m):
            txt = m.group(1)
            url = m.group(2)
            return "\\httplink[%s]{%s}" % (txt, self._esc_url(url))
        return re.sub(r"\[([^\]]+)\]\(([^)]+)\)", repl, s or "")

    def _esc(self, s: Any) -> str:
        t = str(s or "")
        if "\\" in t:  # allow LaTeX macros to passthrough
            return t
        t = re.sub(r"([%&#_$\{\}])", r"\\\1", t)
        t = t.replace("^", "\\textasciicircum{}").replace("~", "\\textasciitilde{}")
        return t



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