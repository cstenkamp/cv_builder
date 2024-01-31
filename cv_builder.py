from pprint import pprint
from datetime import datetime
import re
import yaml

PATH = "/home/chris/Documents/projects/cstenkamp.de/components/cv/all_cvs.yaml"

def main():
    builder = CVBuilder(PATH)
    print(builder.list_variants())
    builder.build_lang_variant("de")


class CVBuilder():
    def __init__(self, path):
        self.path = path
        self.yaml = self.load_yaml()
        self.translations = self.yaml["Translations"]

    def load_yaml(self):
        with open(self.path, "r") as rfile:
            cv = yaml.load(rfile, Loader=yaml.SafeLoader)
        return cv

    def list_variants(self):
        return {k: {v2["name"]: k2 for k2, v2 in v.items()} for k, v in self.yaml["Variants"].items()}

    def get_langs(self):
        return set(self.yaml["Variants"]["Language"].keys())
        # print(cv["Translations"])

    def default_lang(self):
        langs = self.yaml["Variants"]["Language"]
        return [k for k, v in langs.items() if v.get("default")][0]

    def wordwise_translate(self, what, tolang):
        # TODO does not work if there's eg a colon after the word
        transl = self.translations[tolang]
        if isinstance(what, (int, float)):
            what = str(what)
        if isinstance(what, str):
            what = what.replace(":", " :").replace("{", " {")
            what = " ".join([transl.get(i, i) for i in what.split(" ")])
            what = what.replace(" :", ":").replace(" {", "{")
        elif isinstance(what, (list, set, tuple)):
            what = [self.wordwise_translate(i, tolang) for i in what]
        return what

    def hndlval(self, val, lang, key=""):
        assert isinstance(val, (dict, str, int, float, list, tuple, set))
        if isinstance(val, str) and "img(" in val:
            assert re.match(r"img\((.*?)\)", val)[0] == "img("+re.match(r"img\((.*?)\)", val)[1]+")", "if you use 'img(..)', that must be the full value!"
            print("TODO: img")
        if isinstance(val, str) and "date(" in val:
            date = datetime.strptime(re.match(r"date\((.*?)\)", val)[1], "%Y-%m-%d")
            fmtstring = self.yaml["Variants"]["Language"][lang]["datefmt"]
            val = re.sub(r"date\(.*?\)", date.strftime(fmtstring), val)
        result = self.subdict_select_keys(val, lang) if isinstance(val, dict) \
                else self.wordwise_translate(val, lang) if isinstance(val, (str, int, float)) \
                else self.handle_sublist(val, lang) if isinstance(val, (list, tuple, set)) \
                else val
        # now if the key had design-instructions (in curly brackets) add that here
        if re.match(r".*?\{.*?}", key):
            design_info = re.match(r".*?\{(.*?)}", key)[1]
            if isinstance(result, dict):
                result["design"] = design_info
            elif isinstance(result, list):
                result = [f"<!--design: {design_info}-->"]+result
        return result

    def build_lang_variant(self, language, annotate_kind=False):
        cv = {k: v for k, v in self.yaml.items() if k not in ["Variants", "Translations"]}
        ncv = {}
        for k, v in cv.items():
            k = self.wordwise_translate(k, language)
            if not re.match(r".*?\[.*?].*?", k):
                ncv[k] = v
            elif f"[{language}]" in k:
                ncv[re.sub(r"(\[.*?])", "", k).strip()] = v
        cv = {k: self.hndlval(v, language, k) for k, v in ncv.items()}
        cv = {(k if not re.match(r".*?\{(.*?)}", k) else re.match(r"(.*?)\{", k)[1]).strip(): v for k, v in cv.items() if v}
        # pprint(cv, width=200, sort_dicts=False)
        if annotate_kind:
            cv = {k: {"chronog": v} if isinstance(v, list) and all(isinstance(i, dict) for i in v) \
                  else {"lst": v} if isinstance(v, list) \
                  else {"basic": {k2: v2 for k2, v2 in v.items() if k2 != "design"}, "design": v["design"]} if isinstance(v, dict) and "design" in v \
                  else v \
                  for k, v in cv.items()}
        return cv

    def subdict_select_keys(self, di, lang):
        other_langs = self.get_langs() - {lang}
        ndi, removekeys = {}, set()
        for k, v in di.items():
            usekey = (not "_hidden" in k)
            for ola in other_langs:
                usekey = usekey and not (f"_{ola}" in k)
                # am I working with default-lang? if so use `orig_key = k.replace(f"_{ola}", "")`
            if usekey:
                if f"_{lang}" in k: # then don't use the default key
                    removekeys.add(k.replace(f"_{lang}", ""))
                ndi[k] = self.hndlval(v, lang, k)
        di = {}
        # now remove the default keys if we took the _smth keys
        for k, v in ndi.items():
            if k not in removekeys:
                k = self.wordwise_translate(k.replace(f"_{lang}", ""), lang)
                di[k] = self.wordwise_translate(v, lang)
        # now handle the special key "show_on"
        if "show_on" in di:
            if isinstance(di["show_on"], str):
                di["show_on"] = [di["show_on"]]
            if lang in di["show_on"]:
                di = {k: v for k, v in di.items() if k != "show_on"}
            else:
                return {}
        # pprint(di, width=200, sort_dicts=False)
        return di

    def handle_sublist(self, lst, lang):
        if all(isinstance(i, str) for i in lst):
            lst = self.handle_textual_sublist(lst, lang)
        else:
            lst = [self.hndlval(elem, lang) for elem in lst]
        lst = [i for i in lst if i]
        # pprint(lst, width=200, sort_dicts=False)
        return lst

    def handle_textual_sublist(self, lst, lang):
        other_langs = self.get_langs() - {lang}
        nlst = []
        for elem in lst:
            useelem = True
            for ola in other_langs:
                useelem = useelem and not (f"[{ola}]" in elem)
            if useelem:
                if f"[{lang}]" in elem: # then don't use the default key
                    elem = elem.replace(f"[{lang}]", "").strip()
                nlst.append(elem)
        return nlst



if __name__ == '__main__':
    main()