from os.path import dirname, isfile, join, splitext
from os import listdir

from flask import Flask, redirect, url_for, session, make_response, render_template, Response
from flask import request
from flask_cors import CORS, cross_origin
from flask import send_file
from jinja2 import Template

from jinja_cv_html import IGNORE_SECTIONS, SECTIONTRANSLATE, update, inline_edit
from cv_builder import CVBuilder


PATH = "/home/chris/Documents/projects/cstenkamp.de/components/cv/all_cvs.yaml"
IMGROOT = "/home/chris/Documents/projects/cstenkamp.de/components/cv/"
TEMPLATEPATH = "/home/chris/Documents/projects/cstenkamp.de/components/cv_builder/static/cv.html.jinja"

####################################################################################

app = Flask(__name__)
app.config.from_object(__name__)
CORS(app)

@app.errorhandler(404)
def not_found(*args, **kwargs):
    """Page not found."""
    return make_response("Error 404! Page not found.", 404)


@app.before_request
def before_request(*args, **kwargs):
    print(end='')

########################################################################################


def get_variant(args, builder=None):
    builder = builder or CVBuilder(PATH)
    variants = builder.list_variants()
    this_variant = {}
    for var in variants.keys():
        this_variant[var.lower()] = args.get(var.lower()) if args.get(var.lower()) not in [None, "null"] else builder.default_lang()
    return this_variant


def prepare_contentdict(cv_content, cvdir, get_image_url, hugo_public_path, sectiontranslate, ignoresections):
    cnt = cv_content["Basic Info"]
    cnt.update(cvpath = cvdir,
               image_link = f"{get_image_url}?name={cnt['photo'][4:-1]}",
               homepage_link = f"https://{cnt['homepage']}",
               hugo_public_path = hugo_public_path,
               )
    cnt["sections"] = [{"title": v, "sectionkey": k, "content": cv_content[v]}
                         for k, vv in sectiontranslate.items() for v in vv if cv_content.get(v) and k not in ignoresections]
    cnt = update(cnt, fn=inline_edit)
    return cnt

########################################################################################


@app.route('/getimage')
def get_image():
    fname = join(IMGROOT, request.args.get("name"))
    if not isfile(fname):
        fname = [i for i in listdir(IMGROOT) if splitext(i)[0] == request.args.get("name")]
        if len(fname) < 1:
            return ""
        fname = join(IMGROOT, fname[0])
    return send_file(fname, mimetype='image/gif')

@app.route('/cv.css')
def cv_style():
    cssfile = join(dirname(__file__), "static", "cv.css")
    return send_file(cssfile)


@app.route("/listvariants")
@cross_origin(supports_credentials=True)
def list_variants():
    builder = CVBuilder(PATH)
    return builder.list_variants()


@app.route("/getyaml", methods=['GET'])
@cross_origin(supports_credentials=True)
def get_yaml():
    builder = CVBuilder(PATH)
    variant = get_variant(request.args, builder)
    yaml = builder.build_lang_variant(**variant)
    return yaml


@app.route("/getcv", methods=['GET'])
@cross_origin(supports_credentials=True)
def get_cv():
    builder = CVBuilder(PATH)
    variant = get_variant(request.args, builder)
    cv_content = builder.build_lang_variant(**variant, annotate_kind=True)

    with open(TEMPLATEPATH) as rfile:
        tmpl = Template(rfile.read())

    cnt = prepare_contentdict(cv_content=cv_content,
                              cvdir=dirname(PATH),
                              get_image_url="http://localhost:8003/getimage",
                              hugo_public_path="http://localhost:1313",
                              sectiontranslate=SECTIONTRANSLATE,
                              ignoresections=IGNORE_SECTIONS)
    cnt["cv_css_path"] = "http://localhost:8003/cv.css"
    html = tmpl.render(**cnt)

    return html

####################################################################################

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8003)