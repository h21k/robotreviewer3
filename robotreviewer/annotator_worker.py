import zerorpc
import os
import logging

def str2bool(v):
  return v.lower() in ("yes", "true", "t", "1")

DEBUG_MODE = str2bool(os.environ.get("DEBUG", "true"))
LOCAL_PATH = "robotreviewer/uploads"
LOG_LEVEL = (logging.DEBUG if DEBUG_MODE else logging.INFO)

logging.basicConfig(level=LOG_LEVEL, format='[%(levelname)s] %(name)s %(asctime)s: %(message)s')
log = logging.getLogger(__name__)
log.info("Welcome to RobotReviewer :)... annotator process starting")


from robotreviewer.textprocessing.pdfreader import PdfReader
pdf_reader = PdfReader() # launch Grobid process before anything else
import sqlite3
import robotreviewer
from robotreviewer.textprocessing.tokenizer import nlp
from robotreviewer import config
''' robots! '''
# from robotreviewer.robots.bias_robot import BiasRobot
from robotreviewer.robots.rationale_robot import BiasRobot
from robotreviewer.robots.pico_robot import PICORobot
from robotreviewer.robots.rct_robot import RCTRobot
from robotreviewer.robots.pubmed_robot import PubmedRobot
# from robotreviewer.robots.mendeley_robot import MendeleyRobot
# from robotreviewer.robots.ictrp_robot import ICTRPRobot
from robotreviewer.robots import pico_viz_robot
from robotreviewer.robots.pico_viz_robot import PICOVizRobot




rr_sql_conn = sqlite3.connect(robotreviewer.get_data('uploaded_pdfs/uploaded_pdfs.sqlite'), detect_types=sqlite3.PARSE_DECLTYPES)
c = rr_sql_conn.cursor()

c.execute('CREATE TABLE IF NOT EXISTS article(id INTEGER PRIMARY KEY, report_uuid TEXT, pdf_uuid TEXT, pdf_hash TEXT, pdf_file BLOB, pdf_filename TEXT, annotations TEXT, timestamp TIMESTAMP)')
c.close()
rr_sql_conn.commit()

######
## robots to be used are loaded here
######
log.info("Loading the robots...")
bots = {"bias_bot": BiasRobot(top_k=3),
        "pico_bot": PICORobot(),
        "pubmed_bot": PubmedRobot(),
        # "ictrp_bot": ICTRPRobot(),
        "rct_bot": RCTRobot(),
        "pico_viz_bot": PICOVizRobot()}
        # "mendeley_bot": MendeleyRobot()}
log.info("Robots loaded successfully! Ready...")



# lastly wait until Grobid is connected
pdf_reader.connect()

import zerorpc

class AnnotationRPC(object):

    def annotate_task(self, report_uuid):
        c = rr_sql_conn.cursor()
        blobs, article_ids, filenames = [], [], []
        for i, row in enumerate(c.execute("SELECT pdf_uuid, pdf_file, pdf_filename  FROM article WHERE report_uuid=?", (report_uuid,))):
            blobs.append(row[1])
            article_ids.append(row[0])
            filenames.append(row[2])

        articles = pdf_reader.convert_batch(blobs)
        parsed_articles = []
        # tokenize full texts here
        for doc in nlp.pipe((d.get('text', u'') for d in articles), batch_size=1, n_threads=config.SPACY_THREADS, tag=True, parse=True, entity=False):
            parsed_articles.append(doc)

        # adjust the tag, parse, and entity values if these are needed later
        for article, parsed_text in zip(articles, parsed_articles):
            article._spacy['parsed_text'] = parsed_text
        for filename, blob, data, pdf_uuid in zip(filenames, blobs, articles, article_ids):
            data = annotate(data, bot_names=["bias_bot", "pico_bot", "rct_bot", "pico_viz_bot"])
            data.gold['pdf_uuid'] = pdf_uuid
            data.gold['filename'] = filename
            c.execute("UPDATE article SET annotations=? WHERE report_uuid=? AND pdf_uuid=?", (data.to_json(), report_uuid, pdf_uuid))
            rr_sql_conn.commit()
        c.close()
        return json.dumps({"report_uuid": report_uuid,
                           "pdf_uuids": article_ids})

    def annotate(self, data, bot_names=["bias_bot"]):
        #
        # ANNOTATION TAKES PLACE HERE
        # change the line below if you wish to customise or
        # add a new annotator
        #
        annotations = annotation_pipeline(bot_names, data)
        return annotations

    def annotation_pipeline(self, bot_names, data):
        for bot_name in bot_names:
            log.debug("Sending doc to {} for annotation...".format(bots[bot_name].__class__.__name__))
            data = bots[bot_name].annotate(data)
            log.debug("{} done!".format(bots[bot_name].__class__.__name__))
        return data


s = zerorpc.Server(AnnotationRPC())
s.bind("tcp://0.0.0.0:4242")
s.run()
