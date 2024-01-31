import yaml
import re
import argparse
import os.path as p
from shutil import copyfile

PATH = "/home/chris/Documents/CV_Zertifikate_Bewerbungen_Arbeitsvertrage/CV/2021_en_repo_devcontainer/cstenkamp_cv.tex"
extract = lambda txt, elem, index: txt[elem.regs[index][0]:elem.regs[index][1]].strip("\n").strip()

# TODO: see awards in maxlen: I can have the same key (2015) multiple times! second one will be deleted here!

########################################################################################################################
# main

def parse_command_line_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--cvpath', help='Path of your cv-tex-file', default=PATH)
    parser.add_argument('--yamlpath', help='Path of where you want to store the resuling YAML', default="cv.yaml")
    return parser.parse_args()

def main():
    args = parse_command_line_args()
    cv_tex_to_yaml(args.cvpath, args.yamlpath)

def cv_tex_to_yaml(cv_path, yaml_path, do_print=True):
    text = read_remove_superflous(cv_path)
    preamble, content = split_preamble_content(text)
    basic_info = get_basic_info(preamble)
    yaml_dump(basic_info, content, yaml_path)
    if basic_info.get("photo"):
        img = basic_info["photo"][0]+".jpg"
        copyfile(p.join(p.dirname(cv_path), img), p.join(p.dirname(yaml_path), img))
    if do_print:
        print_pretty(basic_info, content)

def yaml_dump(basic_info, content, yamlpath):
    sections = {"Basic Info": basic_info}
    for section_name, section_cont in section_iter(content):
        basic, chronog, lst = parse_cventries(section_cont)
        sections[section_name] = dict(basic=basic, chronog=chronog, lst=lst)
    with open(yamlpath, 'w') as file:
        yaml.dump(sections, file, sort_keys=False, allow_unicode=True)


########################################################################################################################
# simple text processing stuff to get rid of superflous stuff

def find_closing_bracket(text, opening_position):
    stack = []
    for i in range(opening_position, len(text)):
        if text[i] == '{':
            stack.append('{')
        elif text[i] == '}':
            if stack and stack[-1] == '{':
                stack.pop()
            else:
                return i
    return -1

def remove_multiline_cmd(txt, start_regex):
    while (occ := re.search(start_regex, txt)):
        stop_pos = find_closing_bracket(txt, occ.span()[1])
        txt = txt[:occ.span()[0]]+txt[stop_pos+1:]
    return txt

def remove_let(txt):
    while (pos := txt.find("\\let")) >= 0:
        assert txt[pos+4] == "\\"
        second_command = txt[pos+5+(txt[pos+5:].find("\\")):]
        let_endpos = re.search("\W", second_command[1:]).span()[0]+1
        txt = txt[:pos]+second_command[let_endpos:]
    return txt

def prep(txt):
    return "\n".join([line for line in txt.splitlines() if line.strip()])

def read_remove_superflous(path):
    with open(path, "r") as rfile:
        txt = rfile.readlines()
    # remove comments
    txt = [line.strip("\n").rstrip("%") for line in txt if not line.strip().startswith("%")]
    txt = "\n".join(txt).replace("\\%", "THISISANACTUALPERCENTSIGN24046456")
    txt = [line[:line.find("%")].strip() if line.find("%") >= 0 else line for line in txt.splitlines()]
    txt = [line.replace("THISISANACTUALPERCENTSIGN24046456", "%") for line in txt]
    # remove superflous commands
    txt = [line for line in txt if not any(line.startswith(i) for i in ["\\usepackage", "\\PassOptionsToPackage", "\\documentclass", "\\moderncv", "\\maketitle", "\\pagebreak", "\\vfill"])]
    txt = "\n".join([line.strip() for line in txt if line.strip()])
    txt = re.sub(r"\\vspace{.*?}", "", txt)
    txt = re.sub(r"\\setlength{.*?}{.*?}", "", txt)
    txt = remove_multiline_cmd(txt, r"\\(re)?newcommand\*?{.*?}(\[.*?])*\n*({)")
    txt = remove_let(txt)
    return prep(txt)

########################################################################################################################
# actual parsing

def split_preamble_content(txt):
    preamble = txt[:txt.find("\\begin{document}")]
    content = txt[txt.find("\\begin{document}"):]
    content = content[content.find("\n"):]
    content = content[:content.find("\\end{document}")]
    return prep(preamble), prep(content)

def get_basic_info(preamble):
    info_di = {}
    for line in preamble.splitlines():
        linen = parse_format(line)
        # allows for commands with exactly one or two required arguments
        res = (res := re.findall(r"\\(.*?)(\[.*?])*{(.*?)}({(.*?)})?", linen)[0])[0], res[2], res[-1]
        if res[0] == 'extrainfo' and "\\httplink" in line:
            info_di["homepage"] = [re.search(r"\((.*?)\)", res[1]).group(1).replace("https://", "").replace("http://", "")]
        info_di[res[0]] = [i for i in res[1:] if i]
    return info_di

def section_iter(content):
    sections = []
    for section in re.finditer(r"\\section{(.*?)}", content):
        section_name = content[section.regs[1][0]:section.regs[1][1]]
        section_startpos = section.regs[-1][-1]+1
        sections.append([section_name, section_startpos, section])
    for i in range(len(sections) - 1):
        sections[i] = sections[i][:2] + [sections[i+1][2].span()[0]]
    sections[-1] = sections[-1][:2] + [None]
    for sname, startpos, endpos in sections:
        section_cont = prep(content[startpos:endpos])
        # print(sname, "\n  ", ("\n   ".join(section_cont.splitlines())), "\n"*2)
        yield sname, section_cont

def parse_format(txt):
    """parses text-formatting, such as bold or hyperlinks, for example `\textit{\href{https://www.visiolab.io}{visiolab.io}}`"""
    # TODO: unfortunately due to doing this with regex, the order is important - I have to replace inner stuff before outer stuff, that is very error-prone!
    httplinks = [r"\\href{(.*?)}{(.*?)}", r"\\httplink\[(.*?)]{(.*?)}"]
    for lnk in httplinks:
        while (occ := re.search(lnk, txt)):
            txt = txt[:occ.span()[0]] + f"[{extract(txt, occ, 1)}]({extract(txt, occ, 2)})" + txt[occ.span()[1]:]
    while (occ := re.search(r"\\httplink{(.*?)}", txt)):
        txt = txt[:occ.span()[0]] + f"[{extract(txt, occ, 1)}]({('' if extract(txt, occ, 1).startswith('http') else 'https://')+extract(txt, occ, 1)})" + txt[occ.span()[1]:]

    markdown_replacers = dict(textit = "*", textbf = "**", underline = "_", emph = "*", bo = "**", ts = "", textsc = "*")
    for key, val in markdown_replacers.items():
        while (occ := re.search(r"\\"+key+r"{(.*?)}", txt)):
            txt = txt[:occ.span()[0]] + val + extract(txt, occ, 1) + val + txt[occ.span()[1]:]

    remove_commands = [r"\\hyperref\[.*?]{.*?}", r"\\begin{spacing}{.*?}(.*?)\\end{spacing}"] # if smth is in parantheses, this is used. If nothing, completely removed.
    for rm in remove_commands:
        while (occ := re.search(rm, txt, re.DOTALL)):
            if len(occ.regs) > 1 and occ.group(1):
                txt = txt[:occ.span()[0]] + occ.group(1) + txt[occ.span()[1]:]
            else:
                txt = txt[:occ.span()[0]] + txt[occ.span()[1]:]

    if "\\begin{itemize}" in txt:
        while (occ := re.search(r"\\begin{itemize}(.*?)\\end{itemize}", txt, re.DOTALL)):
            txt = txt[:occ.span()[0]].rstrip("\n")+"<newline>" + (occ.group(1).replace("\\item", "\n*")).replace("\n\n", "\n").replace("\n\n", "\n") + txt[occ.span()[1]:].lstrip("\n")

    # replace \newline with line break, but ensure there are no more than two linebreaks after each other
    for linebreak in ["\\newline", "\\\\"]:
        txt = txt.replace(linebreak, "  \n")
    txt = "\n".join([i.strip() for i in txt.splitlines()])
    while txt.find("\n\n") > 0:
        txt = txt.replace("\n\n", "\n")
    txt = txt.replace("<newline>", "\n") # for correct markdown, we NEED an extra \n
    return txt


def parse_cventries(txt):
    """I expect:
     basic key-value stuff:
       \cvitem{key}{val}
       \cvitemwithcomment{key}{val}{comment}
     chronological stuff:
       \cventry{years}{degree/job title}{institution/employer}{localization}{optionnal: grade/...}{optional: comment/job description}
     list stuff:
       \cvlistdoubleitem{item1}{item2}
    """
    txt = parse_format(txt)

    basicelems_di = {}
    for elem in re.finditer(r"\\cvitem{(.*?)}{(.*?)}", txt, re.DOTALL):
        key, val = txt[elem.regs[1][0]:elem.regs[1][1]], txt[elem.regs[2][0]:elem.regs[2][1]]
        val = val.strip() if isinstance(val, str) else [i.strip() for i in val]
        if not key: key = " "
        if val:
            basicelems_di[key.strip()] = val
    for elem in re.finditer(r"\\cvitemwithcomment{(.*?)}{(.*?)}{(.*?)}", txt):
        key, val = txt[elem.regs[1][0]:elem.regs[1][1]], [txt[elem.regs[2][0]:elem.regs[2][1]], txt[elem.regs[3][0]:elem.regs[3][1]]]
        val = val.strip() if isinstance(val, str) else [i.strip() for i in val]
        if not key: key = " "
        if val:
            basicelems_di[key.strip()] = val

    chronological_elems = []
    for elem in re.finditer(r"\\cventry{(.*?)}{(.*?)}{(.*?)}{(.*?)}{(.*?)}{(.*?)}", txt, re.DOTALL):
        chronological_elems.append(dict(
            years = extract(txt, elem, 1), title = extract(txt, elem, 2), employer = extract(txt, elem, 3),
            place = extract(txt, elem, 4), optshort = extract(txt, elem, 5), optlong = extract(txt, elem, 6),
        ))

    list_elems = []
    for elem in re.finditer(r"\\cvlistdoubleitem{(.*?)}{(.*?)}", txt):
        list_elems.extend([i for i in [extract(txt, elem, 1), extract(txt, elem, 2)] if i])

    assert sum((bool(basicelems_di), bool(chronological_elems), bool(list_elems))) == 1, "In each section there should be exactly one of (chronological stuff, key-value-stuff and list-stuff!!)"
    return basicelems_di, chronological_elems, list_elems

########################################################################################################################
# pretty printing

def pretty_dict(di, indent=2):
    txt = ""
    maxln = len(max(di.keys(), key=lambda x: len(x)))
    for key, val in di.items():
        txt += f"{' '*indent}{key.rjust(maxln)}: "
        indenter = "\n"+" "*(indent+maxln+2)
        txt += indenter.join([i.replace("\n", indenter) for i in ([val] if isinstance(val, str) else val)])
        txt += "\n"
    return prep(txt)


def print_pretty(basic_info, main_cont):
    print(f"Basic Info\n{pretty_dict(basic_info)}")
    for section_name, section_cont in section_iter(main_cont):
        basic, chronog, lst = parse_cventries(section_cont)
        print("\n"+section_name)
        if basic:
            print(pretty_dict(basic))
        elif chronog:
            for elem in chronog:
                txt = f'  {elem["years"].ljust(20)} {elem["title"]}, {elem["employer"]}'
                for optional in ["place", "optshort", "optlong"]:
                    if elem[optional]: txt += f', {elem[optional]}'
                print(txt)
        elif lst:
            for elem in lst:
                print(f"  - {elem}")

########################################################################################################################

if __name__ == "__main__":
    main()