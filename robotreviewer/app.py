"""
RobotReviewer server
"""

# Authors:  Iain Marshall <mail@ijmarshall.com>
#           Joel Kuiper <me@joelkuiper.com>
#           Byron Wallace <byron@ccs.neu.edu>

import logging, os
os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3' # remove info message about TF compilation performance
from datetime import datetime, timedelta

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

DEBUG_MODE = str2bool(os.environ.get("DEBUG", "true"))
LOCAL_PATH = "robotreviewer/uploads"
LOG_LEVEL = (logging.DEBUG if DEBUG_MODE else logging.INFO)

logging.basicConfig(level=LOG_LEVEL, format='[%(levelname)s] %(name)s %(asctime)s: %(message)s')
log = logging.getLogger(__name__)
log.info("Welcome to RobotReviewer :)")



from flask import Flask, json, make_response, send_file
from flask import redirect, url_for, jsonify
from flask import request, render_template
from flask_bootstrap import Bootstrap
from robotreviewer.ux.forms import QuestionForm, QuestionForm2

from werkzeug.utils import secure_filename

from flask_wtf.csrf import CsrfProtect

try:
    from cStringIO import StringIO # py2
except ImportError:
    from io import BytesIO as StringIO # py3


''' robots! '''
from robotreviewer.robots.rationale_robot import BiasRobot
from robotreviewer.data_structures import MultiDict

from robotreviewer import config
import robotreviewer

import uuid
from robotreviewer.util import rand_id
import sqlite3

import hashlib
import random

import numpy as np # note - this should probably be moved!

app = Flask(__name__,  static_url_path='')
from robotreviewer import formatting
app.secret_key = os.environ.get("SECRET", "super secret key")
# setting max file upload size 100 mbs
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

csrf = CsrfProtect()
csrf.init_app(app)

Bootstrap(app)


######
## default annotation pipeline defined here
######
log.info("Loading the robots...")
bots = {"bias_bot": BiasRobot}

log.info("Robots loaded successfully! Ready...")

#####
## connect to and set up database
#####
rr_sql_conn = sqlite3.connect(robotreviewer.get_data('uploaded_pdfs/uploaded_pdfs.sqlite'), detect_types=sqlite3.PARSE_DECLTYPES)
c = rr_sql_conn.cursor()

c.execute('CREATE TABLE IF NOT EXISTS article(id INTEGER PRIMARY KEY, report_uuid TEXT, pdf_uuid TEXT, pdf_hash TEXT, pdf_file BLOB, annotations TEXT, timestamp TIMESTAMP, dont_delete INTEGER, timespan TEXT DEFAULT null)')
c.execute('CREATE TABLE IF NOT EXISTS form(id INTEGER PRIMARY KEY, ux_uuid VARCHAR(21), pdf_uuid TEXT, first_question TEXT, second_question VARCHAR(21), third_question VARCHAR(21), flag INTEGER, F1 INTEGER, F2 INTEGER, F3 INTEGER, F4 INTEGER, F5 INTEGER, F6 INTEGER, F7 INTEGER, F8 INTEGER, F9 INTEGER, F10 INTEGER, F11 INTEGER, F12 INTEGER, F13 INTEGER, F14 INTEGER, F15 INTEGER, F16 INTEGER, T1 TEXT)')
c.execute('CREATE TABLE IF NOT EXISTS links(id INTEGER PRIMARY KEY, list_urls TEXT, username TEXT, flag TEXT)')
c.close()
rr_sql_conn.commit()


@app.route('/doc/')
def main():
    resp = make_response(render_template('index.html'))
    return resp

@app.route('/', methods=['GET', 'POST'])
def ux():
    # Here is the random user ID generated by some random function but
    # can be set to some string to test:
    ux_uuid = rand_id() #ID generated from function in util.py
    #print("CHECK")
    #print('___________________________')
    #print(ux_uuid)
    #print('___________________________')

    c = rr_sql_conn.cursor()
    c.execute("SELECT report_uuid, pdf_uuid FROM article WHERE dont_delete='2'")
    a = c.fetchall()

    s = []
    u = 0
    username = ux_uuid
    g = [seq[0]+'/'+seq[1] for seq in a]
    list_urls = random.sample(g, 4)


    #PLACEHOLDER
    display_pdfs = [1,0,0,1]
    random.shuffle(display_pdfs)
    flag = ''.join(map(str, display_pdfs))


    for i in list_urls:
        s.append({"link" : "%s%s%s" % ('/doc/#document/', list_urls[u], '?annotation_type=bias_bot'), "ux_user" : ux_uuid})
        u = u + 1
    p = {}
    p["link_meta"] = s

    c = rr_sql_conn.cursor()
    c.execute("INSERT INTO links(list_urls, username, flag) VALUES(?, ?, ?)", (json.dumps(p), username, str(flag)))
    rr_sql_conn.commit()
    c.close()


    return render_template('ux.html', ux_uuid=ux_uuid)

@app.route('/form1/<ux_uuid>', methods=['GET', 'POST'])
def form1(ux_uuid):
    search_id = ux_uuid
    #print('SEARCH ID >>>>>>>>> ::::: ', search_id)
    pdf_uuids = 'Ada'
    f = 2
    form = QuestionForm()

    if request.method == 'POST':
        if form.validate() == False:
            #print("VALIDATE ME !")
            return render_template('/form1.html', form=form, ux_uuid=ux_uuid)
        else:
            #print("CHECKPOINT BETA")
            #print('___________________________')
            #print(ux_uuid, type(ux_uuid))
            #print(form.first_question.data, type(form.first_question.data))
            #print(form.second_question.data, type(form.second_question.data))
            #print(form.third_question.data, type(form.third_question.data))
            #print(f, type(f))
            mylist = json.dumps(form.first_question)
            #print('___________________________')
            c = rr_sql_conn.cursor()
            c.execute("INSERT INTO form(ux_uuid, pdf_uuid, first_question, second_question, third_question, flag) VALUES (?, ?, ?, ?, ?, ?)", (ux_uuid, pdf_uuids, mylist, form.second_question.data, form.third_question.data, f))
            rr_sql_conn.commit()
            c.close()

            #checking the ux_uuid and links transferred correctly
            #c = rr_sql_conn.cursor()
            #c.execute("SELECT list_urls FROM links WHERE username = ?", (search_id,))
            #a = c.fetchall()
            #c.close()
            #print(a)


            #return redirect(url_for('ux'))
            #return render_template('video.html', ux_uuid=ux_uuid)
            return redirect(url_for('video', ux_uuid=ux_uuid))

    elif request.method == 'GET':
        #print('path two taken')
        return render_template('form1.html', form=form, ux_uuid=ux_uuid)


    return render_template('form1.html')

@app.route('/video/<ux_uuid>', methods=['GET', 'POST'])
def video(ux_uuid):
    c = rr_sql_conn.cursor()
    c.execute("SELECT list_urls, flag FROM links WHERE username = ?", (ux_uuid,))
    a = c.fetchone()
    links = json.loads(a[0])
    task_ids = list(str(a[1]))

    for i, j in zip(links["link_meta"], task_ids):
        url = i["link"] + '&ux_uuid=' + i["ux_user"] + '&flag=1&task_id=' + j
        break
    #print(url)
    return render_template('video.html', ux_uuid=ux_uuid, doc_url=url)


@app.route('/form2/<ux_uuid>', methods=['GET', 'POST'])
def form2(ux_uuid):

    form = QuestionForm2()

    if request.method == 'POST':
        if form.validate() == False:
            #print("VALIDATE ME !")
            return render_template('/form2.html', form=form, ux_uuid=ux_uuid)
        else:
            #print("CHECKPOINT GAMMA")
            #print('_________________')
            #print('VVVVVVVVVVVVVVVVV')
            #print(ux_uuid, type(ux_uuid))
            #print(form.first_sus.data, type(form.first_sus.data))
            #print(form.second_sus.data, type(form.second_sus.data))
            #print(form.third_sus.data, type(form.third_sus.data))
            #print(form.seventeenth_sus.data, type(form.seventeenth_sus.data))
            #print('=================================')
            c = rr_sql_conn.cursor()
            c.execute("UPDATE form SET F1=?, F2=?, F3=?, F4=?, F5=?, F6=?, F7=?, F8=?, F9=?, F10=?, F11=?, F12=?, F13=?, F14=?, F15=?, F16=?, T1=? WHERE ux_uuid=?", (form.first_sus.data, form.second_sus.data, form.third_sus.data, form.fourth_sus.data, form.fifth_sus.data, form.sixth_sus.data, form.seventh_sus.data, form.eighth_sus.data, form.ninth_sus.data, form.tenth_sus.data, form.eleventh_sus.data, form.twelfth_sus.data, form.thirteenth_sus.data, form.fourteenth_sus.data, form.fifteenth_sus.data, form.sixteenth_sus.data, form.seventeenth_sus.data, ux_uuid))
            rr_sql_conn.commit()
            c.close()

            return render_template('blank.html', ux_uuid=ux_uuid)

    elif request.method == 'GET':
        #print('path two taken')
        return render_template('form2.html', form=form, ux_uuid=ux_uuid)

    return render_template('form2.html')


@app.route('/blank', methods=['GET', 'POST'])
def blank():
    ux_uuid = request.args['ux_uuid']

    form = QuestionForm2()

    if request.method == 'POST':
        if form.validate() == False:
            #print("VALIDATE ME !")
            return render_template('/form2.html', form=form, ux_uuid=ux_uuid)
        else:
            #
            #mylist = json.dumps(form.first_question)
            #print('I STORED ALL THE FORM DATA IN THE SQLITE3 DB here - and GO ON TO:')
            return render_template('blank.html', ux_uuid=ux_uuid)

    elif request.method == 'GET':
        #print('path two taken')
        return render_template('form2.html', form=form, ux_uuid=ux_uuid)

    return render_template('form2.html')



@app.errorhandler(413)
def request_entity_too_large(error):
    ''' @TODO not sure if we want to return something else here? '''
    return json.dumps({'success':False, 'error':True}), 413, {'ContentType':'application/json'}



@app.route('/pdf/<report_uuid>/<pdf_uuid>')
def get_pdf(report_uuid, pdf_uuid):
    # returns PDF binary from database by pdf_uuid
    # where the report_uuid also matches
    c = rr_sql_conn.cursor()
    c.execute("SELECT pdf_file FROM article WHERE report_uuid=? AND pdf_uuid=?", (report_uuid, pdf_uuid))
    pdf_file = c.fetchone()
    strIO = StringIO()
    strIO.write(pdf_file[0])
    strIO.seek(0)
    return send_file(strIO,
                     attachment_filename="%s.pdf" % pdf_uuid,
                     as_attachment=False)


@app.route('/marginalia/<report_uuid>/<pdf_uuid>', methods=['POST','GET'])
def get_marginalia(report_uuid, pdf_uuid):
    # calculates marginalia from database by pdf_uuid
    # where the report_uuid also matches
    annotation_type = request.args["annotation_type"]
    ux_uuid = request.args["ux_uuid"]
    task_id = int(request.args["task_id"])
    c = rr_sql_conn.cursor()
    c.execute("SELECT annotations FROM article WHERE report_uuid=? AND pdf_uuid=?", (report_uuid, pdf_uuid))
    annotation_json = c.fetchone()
    data = MultiDict()
    data.load_json(annotation_json[0])
    structured_data = []
    if bool(data.ml):
        if len(data.ml["bias"]):
            for row in data.ml["bias"]:
                annotation_metadata = []
                for sent in row["annotations"]:
                    if sent["uuid"] == ux_uuid or ('default' in sent["uuid"] and task_id == 1):
                        annotation_metadata.append({"content" : sent["content"],
                                                "position" : sent["position"],
                                                "uuid"  : sent["uuid"],
                                                "prefix" : sent["prefix"],
                                                "suffix" : sent["suffix"]})
                find = True
                judge = ""
                for judgement in row["judgement"]:
                    if judgement["uuid"] == ux_uuid:
                        judge = judgement["judgement"]
                        find = False
                        break;
                    elif find and task_id==1 and judgement["uuid"] == "default":
                        judge = judgement["judgement"]
                structured_data.append({"domain" : row["domain"],
                                    "judgement" : judge,
                                    "annotations" : annotation_metadata})
            data.ml["bias"] = structured_data
    marginalia = bots[annotation_type].get_marginalia(data)
    return json.dumps(marginalia)

@csrf.exempt # TODO: add csrf back in
@app.route('/savemarginalia/<report_uuid>/<pdf_uuid>/<ux_uuid>', methods=['POST'])
def savemarginalia(report_uuid, pdf_uuid, ux_uuid):
    marginalia = request.form['data']
    conn = sqlite3.connect(robotreviewer.get_data('uploaded_pdfs/uploaded_pdfs.sqlite'), detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    c.execute("SELECT annotations FROM article WHERE report_uuid=? AND pdf_uuid=?", (report_uuid, pdf_uuid))
    annotation_json = c.fetchone()
    data = MultiDict()
    data.load_json(annotation_json[0])
    structured_data_d = []
    for row_d in data.ml['bias']:
        annotation_d_metadata = []
        for sent in row_d["annotations"]:
            if sent["uuid"] != ux_uuid:
                annotation_d_metadata.append({"content" : sent["content"],
                                        "position" : sent["position"],
                                        "uuid"  : sent["uuid"],
                                        "prefix" : sent["prefix"],
                                        "suffix" : sent["suffix"]})
        judgement_data = []
        for judgement in row_d["judgement"]:
            if judgement["uuid"] != ux_uuid:
                judgement_data.append({"uuid" : judgement["uuid"],
                                        "judgement" : judgement["judgement"]})
        structured_data_d.append({"judgement" : judgement_data,
                                    "annotations" : annotation_d_metadata})
    datam = MultiDict()
    datam.load_json(marginalia)
    structured_data = []
    for row in datam.marginalia:
        bias_class = row["description"].replace("**Overall risk of bias prediction**:","")
        if bias_class=="high" or bias_class=="unclear" or bias_class=="low":
            bias_class = bias_class
        else:
            bias_class = ""
        annotation_metadata = []
        for sent in row["annotations"]:
            if sent["uuid"] == ux_uuid:
                annotation_metadata.append({"content" : sent["content"],
                                            "position" : sent["position"],
                                            "uuid"  : sent["uuid"],
                                            "prefix" : sent["prefix"],
                                            "suffix" : sent["suffix"]})
        judgement_data_d = [{"uuid" : ux_uuid,
                                "judgement" : bias_class}]
        structured_data.append({"domain" : row["title"],
                                "judgement" : judgement_data_d,
                                "annotations" : annotation_metadata})
    structured_data_all = []
    for i , j in zip(structured_data, structured_data_d):
        structured_data_all.append({"domain" : i["domain"],
                                    "judgement" : i["judgement"] + j["judgement"],
                                    "annotations" : i["annotations"] + j["annotations"]})
    # ml = bots['bias_bot'].get_marginalia(datam)
    data.ml['bias'] = structured_data_all
    cn = conn.cursor()
    cn.execute("UPDATE article SET annotations = ? WHERE report_uuid=? AND pdf_uuid=?", (data.to_json(), report_uuid, pdf_uuid))
    conn.commit()
    conn.close()
    return json.dumps(datam.to_json())

@csrf.exempt # TODO: add csrf back in
@app.route('/submit_time/<report_uuid>/<pdf_uuid>/<ux_uuid>', methods=['POST'])
def submit_time(report_uuid, pdf_uuid, ux_uuid):
    spent_time = int(request.form['data'])
    time_data = []
    conn = sqlite3.connect(robotreviewer.get_data('uploaded_pdfs/uploaded_pdfs.sqlite'), detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    c.execute("SELECT timespan FROM article WHERE report_uuid=? AND pdf_uuid=?", (report_uuid, pdf_uuid))
    elapse = c.fetchone()
    time_data = []
    if elapse[0]:
        t_data = json.loads(elapse[0])
        has_entry = False
        for row in t_data:
            if row["uuid"] == ux_uuid:
                total_time = spent_time
                has_entry = True
            else:
                total_time = row["time"]
            time_data.append({"uuid" : row["uuid"],"time" : total_time})
        if has_entry:
            pass
        else:
            time_data.append({"uuid" : ux_uuid, "time" : spent_time})
    else:
        time_data.append({"uuid" : ux_uuid,"time" : spent_time})
    c.execute("UPDATE article SET timespan = ? WHERE report_uuid=? AND pdf_uuid=?", (json.dumps(time_data), report_uuid, pdf_uuid))
    conn.commit()
    conn.close()
    return json.dumps(spent_time)

@csrf.exempt # TODO: add csrf back in
@app.route('/get_time/<report_uuid>/<pdf_uuid>/<ux_uuid>', methods=['POST'])
def get_time(report_uuid, pdf_uuid, ux_uuid):
    c = rr_sql_conn.cursor()
    c.execute("SELECT timespan FROM article WHERE report_uuid=? AND pdf_uuid=?", (report_uuid, pdf_uuid))
    elapse = c.fetchone()
    #t_data = json.loads(elapse[0])
    timespan = 0
    if(elapse[0]):
        t_data = json.loads(elapse[0])
        for row in t_data:
            if row["uuid"] == ux_uuid:
                timespan = row["time"]
    return json.dumps(timespan)

@csrf.exempt # TODO: add csrf back in
@app.route('/get_next/<pdf_uuid>', methods=['POST','GET'])
def next_link(pdf_uuid):
    ux_uuid = request.args["ux_uuid"]
    flag = int(request.args["flag"])
    c = rr_sql_conn.cursor()
    c.execute("SELECT list_urls, flag FROM links WHERE username = ?", (ux_uuid,))
    a = c.fetchone()
    links = json.loads(a[0])
    url = str('#')
    task_ids = list(str(a[1]))
    if len(links["link_meta"]) == flag:
        url = '/blank?ux_uuid=' + ux_uuid
    else:
        j = 0
        for i, k in zip(links["link_meta"], task_ids):
            if j == flag:
                flag = flag + 1
                url = i["link"] + '&ux_uuid=' + i["ux_user"] + '&flag=' + str(flag) + '&task_id=' + k
                break
            else:
                j = j + 1
    return json.dumps(url)


def cleanup_database(days=1):
    """
    remove any PDFs which have been here for more than
    1 day, then compact the database
    """
    log.info('Cleaning up database')
    conn = sqlite3.connect(robotreviewer.get_data('uploaded_pdfs/uploaded_pdfs.sqlite'),
                           detect_types=sqlite3.PARSE_DECLTYPES)

    d = datetime.now() - timedelta(days=days)
    c = conn.cursor()
    c.execute("DELETE FROM article WHERE timestamp < datetime(?) AND dont_delete=0", [d])
    conn.commit()
    conn.execute("VACUUM") # make the database smaller again
    conn.commit()
    conn.close()


try:
    from apscheduler.schedulers.background import BackgroundScheduler

    @app.before_first_request
    def initialize():
        log.info("Initializing clean-up task")
        scheduler = BackgroundScheduler()
        scheduler.start()
        scheduler.add_job(cleanup_database, 'interval', hours=12)

except Exception:
    log.warn("Could not start scheduled clean-up task")
