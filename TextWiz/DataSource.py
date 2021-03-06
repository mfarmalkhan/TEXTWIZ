from builtins import set

import matplotlib
from dateutil.rrule import weekday

matplotlib.use("Qt5Agg")
import numpy as np
from numpy import arange, sin, pi
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt

from Query import *
from pyglet import *

from Cases import *
from Sentiments import *
from stat import *
from bs4 import BeautifulSoup
from urllib.parse import urlparse, urlencode, parse_qs
from textblob import TextBlob
from nltk.tokenize import sent_tokenize
from nltk.stem import WordNetLemmatizer
from nltk.stem import PorterStemmer
from operator import itemgetter

import platform, urllib, requests, cv2, pytesseract, string, re, ntpath, pyglet, os, time, csv, random

#PDF, Word, Twitter
import docx2txt, PyPDF2, tweepy, httplib2

#Youtube
from Youtube.URL import *
import google.auth.exceptions
try:
    YoutubeServerNotFoundError = False
    from Youtube.KeyWord import *
except httplib2.ServerNotFoundError:
    YoutubeServerNotFoundError = True
except google.auth.exceptions.RefreshError:
    print("Done")
except Exception as e:
    print(str(e))

#Audio
import wave
from pydub import AudioSegment

os.environ["PATH"] += os.pathsep + 'ffmpeg/bin/'
from ffmpeg import *

import speech_recognition as sr

class DataSource():
    def __init__(self, path, ext):
        super().__init__()
        self.DataSourcePath = path

        if ext == "Image files (*.png *.bmp *.jpeg *.jpg *.webp *.tiff *.tif *.pfm *.jp2 *.hdr *.pic *.exr *.ras *.sr *.pbm *.pgm *.ppm *.pxm *.pnm)":
            self.DataSourceName = ntpath.basename(path[0])
        elif ext == "URL" or ext ==  'Tweet' or ext ==  'Youtube':
            self.DataSourceName = path
        else:
            self.DataSourceName = ntpath.basename(path)

        self.DataSourceext = ext
        self.DataSourcetext = ""
        self.DataSourceLoadError = False
        self.QueryList = []
        self.CasesList = []
        self.SentimentList = []
        self.VisualizationList = []
        self.AutomaticSentimentList = []

        if(ext == "Doc files (*.doc *.docx)"):
            self.WordDataSource()
        elif(ext == "Pdf files (*.pdf)"):
            self.PDFDataSource()
        elif(ext == "Notepad files (*.txt)"):
            self.TxtDataSource()
        elif(ext == "Rich Text Format files (*.rtf)"):
            self.rtfDataSource()
        elif(ext == "Audio files (*.wav *.mp3)"):
            self.AudioDataSource()
        elif(ext == "Image files (*.png *.bmp *.jpeg *.jpg *.webp *.tiff *.tif *.pfm *.jp2 *.hdr *.pic *.exr *.ras *.sr *.pbm *.pgm *.ppm *.pxm *.pnm)"):
            self.ImageDataSource()
        elif(ext == 'URL'):
            self.WebDataSource()

        self.CreatSentiments()

    # Word File
    def WordDataSource(self):
        try:
            if self.DataSourcePath.endswith('.docx'):
                self.DataSourcetext = docx2txt.process(self.DataSourcePath)
                self.DataSourceLoadError = False
            else:
                if platform.system() == "Windows":
                    import win32com.client as win32
                    from win32com.client import constants

                    word = win32.gencache.EnsureDispatch('Word.Application')
                    doc = word.Documents.Open(self.DataSourcePath)

                    # Rename path with .docx
                    new_file_abs = os.path.abspath(self.DataSourcePath)

                    new_file_abs = re.sub(r'\.\w+$', '.docx', new_file_abs)

                    # Save and Close
                    word.ActiveDocument.SaveAs(
                        new_file_abs, FileFormat=constants.wdFormatXMLDocument
                    )
                    doc.Close(False)

                    self.DataSourcetext = docx2txt.process(new_file_abs)
                    self.DataSourceLoadError = False

                    os.remove(new_file_abs)

                elif platform.system() == "Linux":
                    import textract
                    self.DataSourcetext = textract.process(self.DataSourcePath).decode("utf-8")

        except Exception as e:
            self.DataSourceLoadError = True

        if not self.DataSourceLoadError:
            st = os.stat(self.DataSourcePath)
            self.DataSourceSize = st[ST_SIZE]
            self.DataSourceAccessTime = time.asctime(time.localtime(st[ST_ATIME]))
            self.DataSourceModifiedTime = time.asctime(time.localtime(st[ST_MTIME]))
            self.DataSourceChangeTime = time.asctime(time.localtime(st[ST_CTIME]))

    # PDF File
    def PDFDataSource(self):
        try:
            pdfReader = PyPDF2.PdfFileReader(self.DataSourcePath)
            for page in range(pdfReader.getNumPages()):
                curr_page = pdfReader.getPage(page)
                self.DataSourcetext = self.DataSourcetext + curr_page.extractText()

            self.DataSourceLoadError = False
        except Exception as e:
            self.DataSourceLoadError = True

        if not self.DataSourceLoadError:
            st = os.stat(self.DataSourcePath)
            self.DataSourceSize = st[ST_SIZE]
            self.DataSourceAccessTime = time.asctime(time.localtime(st[ST_ATIME]))
            self.DataSourceModifiedTime = time.asctime(time.localtime(st[ST_MTIME]))
            self.DataSourceChangeTime = time.asctime(time.localtime(st[ST_CTIME]))

    # TXT File
    def TxtDataSource(self):
        try:
            file = open(self.DataSourcePath, 'r', encoding='utf-8')
            self.DataSourcetext = file.read();
            self.DataSourceLoadError = False
        except Exception as e:
            self.DataSourceLoadError = True

        if not self.DataSourceLoadError:
            st = os.stat(self.DataSourcePath)
            self.DataSourceSize = st[ST_SIZE]
            self.DataSourceAccessTime = time.asctime(time.localtime(st[ST_ATIME]))
            self.DataSourceModifiedTime = time.asctime(time.localtime(st[ST_MTIME]))
            self.DataSourceChangeTime = time.asctime(time.localtime(st[ST_CTIME]))

    # RTF File
    def rtfDataSource(self):
        try:
            file = open(self.DataSourcePath, 'r')
            self.DataSourcetext = self.RTFtoPlainText(file.read())
            self.DataSourceLoadError = False
        except Exception as e:
            self.DataSourceLoadError = True

        if not self.DataSourceLoadError:
            st = os.stat(self.DataSourcePath)
            self.DataSourceSize = st[ST_SIZE]
            self.DataSourceAccessTime = time.asctime(time.localtime(st[ST_ATIME]))
            self.DataSourceModifiedTime = time.asctime(time.localtime(st[ST_MTIME]))
            self.DataSourceChangeTime = time.asctime(time.localtime(st[ST_CTIME]))

    # RTFtoPlainText
    def RTFtoPlainText(self, text):
        pattern = re.compile(r"\\([a-z]{1,32})(-?\d{1,10})?[ ]?|\\'([0-9a-f]{2})|\\([^a-z])|([{}])|[\r\n]+|(.)", re.I)
        # control words which specify a "destionation".
        destinations = frozenset((
            'aftncn', 'aftnsep', 'aftnsepc', 'annotation', 'atnauthor', 'atndate', 'atnicn', 'atnid',
            'atnparent', 'atnref', 'atntime', 'atrfend', 'atrfstart', 'author', 'background',
            'bkmkend', 'bkmkstart', 'blipuid', 'buptim', 'category', 'colorschememapping',
            'colortbl', 'comment', 'company', 'creatim', 'datafield', 'datastore', 'defchp', 'defpap',
            'do', 'doccomm', 'docvar', 'dptxbxtext', 'ebcend', 'ebcstart', 'factoidname', 'falt',
            'fchars', 'ffdeftext', 'ffentrymcr', 'ffexitmcr', 'ffformat', 'ffhelptext', 'ffl',
            'ffname', 'ffstattext', 'field', 'file', 'filetbl', 'fldinst', 'fldrslt', 'fldtype',
            'fname', 'fontemb', 'fontfile', 'fonttbl', 'footer', 'footerf', 'footerl', 'footerr',
            'footnote', 'formfield', 'ftncn', 'ftnsep', 'ftnsepc', 'g', 'generator', 'gridtbl',
            'header', 'headerf', 'headerl', 'headerr', 'hl', 'hlfr', 'hlinkbase', 'hlloc', 'hlsrc',
            'hsv', 'htmltag', 'info', 'keycode', 'keywords', 'latentstyles', 'lchars', 'levelnumbers',
            'leveltext', 'lfolevel', 'linkval', 'list', 'listlevel', 'listname', 'listoverride',
            'listoverridetable', 'listpicture', 'liststylename', 'listtable', 'listtext',
            'lsdlockedexcept', 'macc', 'maccPr', 'mailmerge', 'maln', 'malnScr', 'manager', 'margPr',
            'mbar', 'mbarPr', 'mbaseJc', 'mbegChr', 'mborderBox', 'mborderBoxPr', 'mbox', 'mboxPr',
            'mchr', 'mcount', 'mctrlPr', 'md', 'mdeg', 'mdegHide', 'mden', 'mdiff', 'mdPr', 'me',
            'mendChr', 'meqArr', 'meqArrPr', 'mf', 'mfName', 'mfPr', 'mfunc', 'mfuncPr', 'mgroupChr',
            'mgroupChrPr', 'mgrow', 'mhideBot', 'mhideLeft', 'mhideRight', 'mhideTop', 'mhtmltag',
            'mlim', 'mlimloc', 'mlimlow', 'mlimlowPr', 'mlimupp', 'mlimuppPr', 'mm', 'mmaddfieldname',
            'mmath', 'mmathPict', 'mmathPr', 'mmaxdist', 'mmc', 'mmcJc', 'mmconnectstr',
            'mmconnectstrdata', 'mmcPr', 'mmcs', 'mmdatasource', 'mmheadersource', 'mmmailsubject',
            'mmodso', 'mmodsofilter', 'mmodsofldmpdata', 'mmodsomappedname', 'mmodsoname',
            'mmodsorecipdata', 'mmodsosort', 'mmodsosrc', 'mmodsotable', 'mmodsoudl',
            'mmodsoudldata', 'mmodsouniquetag', 'mmPr', 'mmquery', 'mmr', 'mnary', 'mnaryPr',
            'mnoBreak', 'mnum', 'mobjDist', 'moMath', 'moMathPara', 'moMathParaPr', 'mopEmu',
            'mphant', 'mphantPr', 'mplcHide', 'mpos', 'mr', 'mrad', 'mradPr', 'mrPr', 'msepChr',
            'mshow', 'mshp', 'msPre', 'msPrePr', 'msSub', 'msSubPr', 'msSubSup', 'msSubSupPr', 'msSup',
            'msSupPr', 'mstrikeBLTR', 'mstrikeH', 'mstrikeTLBR', 'mstrikeV', 'msub', 'msubHide',
            'msup', 'msupHide', 'mtransp', 'mtype', 'mvertJc', 'mvfmf', 'mvfml', 'mvtof', 'mvtol',
            'mzeroAsc', 'mzeroDesc', 'mzeroWid', 'nesttableprops', 'nextfile', 'nonesttables',
            'objalias', 'objclass', 'objdata', 'object', 'objname', 'objsect', 'objtime', 'oldcprops',
            'oldpprops', 'oldsprops', 'oldtprops', 'oleclsid', 'operator', 'panose', 'password',
            'passwordhash', 'pgp', 'pgptbl', 'picprop', 'pict', 'pn', 'pnseclvl', 'pntext', 'pntxta',
            'pntxtb', 'printim', 'private', 'propname', 'protend', 'protstart', 'protusertbl', 'pxe',
            'result', 'revtbl', 'revtim', 'rsidtbl', 'rxe', 'shp', 'shpgrp', 'shpinst',
            'shppict', 'shprslt', 'shptxt', 'sn', 'sp', 'staticval', 'stylesheet', 'subject', 'sv',
            'svb', 'tc', 'template', 'themedata', 'title', 'txe', 'ud', 'upr', 'userprops',
            'wgrffmtfilter', 'windowcaption', 'writereservation', 'writereservhash', 'xe', 'xform',
            'xmlattrname', 'xmlattrvalue', 'xmlclose', 'xmlname', 'xmlnstbl',
            'xmlopen',
        ))
        # Translation of some special characters.
        specialchars = {
            'par': '\n',
            'sect': '\n\n',
            'page': '\n\n',
            'line': '\n',
            'tab': '\t',
            'emdash': '\u2014',
            'endash': '\u2013',
            'emspace': '\u2003',
            'enspace': '\u2002',
            'qmspace': '\u2005',
            'bullet': '\u2022',
            'lquote': '\u2018',
            'rquote': '\u2019',
            'ldblquote': '\201C',
            'rdblquote': '\u201D',
        }
        stack = []
        ignorable = False  # Whether this group (and all inside it) are "ignorable".
        ucskip = 1  # Number of ASCII characters to skip after a unicode character.
        curskip = 0  # Number of ASCII characters left to skip
        out = []  # Output buffer.
        for match in pattern.finditer(text):
            word, arg, hex, char, brace, tchar = match.groups()
            if brace:
                curskip = 0
                if brace == '{':
                    # Push state
                    stack.append((ucskip, ignorable))
                elif brace == '}':
                    # Pop state
                    ucskip, ignorable = stack.pop()
            elif char:  # \x (not a letter)
                curskip = 0
                if char == '~':
                    if not ignorable:
                        out.append('\xA0')
                elif char in '{}\\':
                    if not ignorable:
                        out.append(char)
                elif char == '*':
                    ignorable = True
            elif word:  # \foo
                curskip = 0
                if word in destinations:
                    ignorable = True
                elif ignorable:
                    pass
                elif word in specialchars:
                    out.append(specialchars[word])
                elif word == 'uc':
                    ucskip = int(arg)
                elif word == 'u':
                    c = int(arg)
                    if c < 0: c += 0x10000
                    if c > 127:
                        out.append(chr(c))  # NOQA
                    else:
                        out.append(chr(c))
                    curskip = ucskip
            elif hex:  # \'xx
                if curskip > 0:
                    curskip -= 1
                elif not ignorable:
                    c = int(hex, 16)
                    if c > 127:
                        out.append(chr(c))  # NOQA
                    else:
                        out.append(chr(c))
            elif tchar:
                if curskip > 0:
                    curskip -= 1
                elif not ignorable:
                    out.append(tchar)
        return ''.join(out)

    # Audio File
    def AudioDataSource(self):
        try:
            self.DataSourceLoadError = False

            if str(self.DataSourcePath).lower().endswith('.mp3'):
                self.converttowav(self.DataSourcePath)
                self.ConvertedAudioPath = os.getcwd() + "\CAudio.wav"

            r = sr.Recognizer()

            if str(self.DataSourcePath).lower().endswith('.wav'):
                hellow = sr.AudioFile(self.DataSourcePath)
            else:
                hellow = sr.AudioFile(self.ConvertedAudioPath)

            with hellow as source:
                audioX = r.record(source)

            try:
                self.DataSourcetext = r.recognize_wit(audioX, "DE4XGSVUN6PC3L3TWBSR7XIIKXGBYSVI")
                print(self.DataSourcetext)
            except Exception as e:
                print(str(e))

            if str(self.DataSourcePath).lower().endswith('.mp3'):
                os.remove(self.ConvertedAudioPath)

        except Exception as e:
            print(str(e))
            self.DataSourceLoadError = True

        if not self.DataSourceLoadError:
            st = os.stat(self.DataSourcePath)
            self.DataSourceSize = st[ST_SIZE]
            self.DataSourceAccessTime = time.asctime(time.localtime(st[ST_ATIME]))
            self.DataSourceModifiedTime = time.asctime(time.localtime(st[ST_MTIME]))
            self.DataSourceChangeTime = time.asctime(time.localtime(st[ST_CTIME]))

    # Audio Convert to .wav
    def converttowav(self, audiopath):
        audiotowav = AudioSegment.from_mp3(audiopath)
        audiotowav.export(os.getcwd() + "\CAudio.wav", format="wav")

    # Image File
    def ImageDataSource(self):
        try:
            pytesseract.pytesseract.tesseract_cmd = 'Tesseract-OCR/tesseract.exe'
            self.DataSourceImage = []
            self.DataSourcetext = ""

            for paths in self.DataSourcePath:
                dummyImage = cv2.imread(paths)
                self.DataSourceImage.append(dummyImage)
                self.DataSourcetext += pytesseract.image_to_string(dummyImage)

            self.DataSourceLoadError = False
        except Exception as e:
            self.DataSourceLoadError = True

        if not self.DataSourceLoadError:
            self.DataSourceSize = []
            self.DataSourceAccessTime = []
            self.DataSourceModifiedTime = []
            self.DataSourceChangeTime = []

            for paths in self.DataSourcePath:
                st = os.stat(paths)
                self.DataSourceSize.append(st[ST_SIZE])
                self.DataSourceAccessTime.append(time.asctime(time.localtime(st[ST_ATIME])))
                self.DataSourceModifiedTime.append(time.asctime(time.localtime(st[ST_MTIME])))
                self.DataSourceChangeTime.append(time.asctime(time.localtime(st[ST_CTIME])))

    # Add Image
    def AddImage(self, ImagePaths):
        self.AddImagePathDoublingError = []
        self.AddImagePathDouble = []

        pytesseract.pytesseract.tesseract_cmd = 'Tesseract-OCR/tesseract.exe'


        for imgPth in ImagePaths:
            imgPthError = False

            for pth in self.DataSourcePath:
                if imgPth == pth:
                    self.AddImagePathDoublingError.append(True)
                    self.AddImagePathDouble.append(pth)
                    imgPthError = True
                    break

            if not imgPthError:
                dummyImage = cv2.imread(imgPth)
                self.DataSourceImage.append(dummyImage)
                self.DataSourcetext += pytesseract.image_to_string(dummyImage)

                self.DataSourcePath.append(imgPth)

                st = os.stat(imgPth)
                self.DataSourceSize.append(st[ST_SIZE])
                self.DataSourceAccessTime.append(time.asctime(time.localtime(st[ST_ATIME])))
                self.DataSourceModifiedTime.append(time.asctime(time.localtime(st[ST_MTIME])))
                self.DataSourceChangeTime.append(time.asctime(time.localtime(st[ST_CTIME])))

    # CSV File
    def CSVDataSource(self, HeaderLabel, CSVPathFlag):
        try:
            self.CSVHeader = HeaderLabel
            self.CSVPathFlag = CSVPathFlag
            self.CSVHeaderLabel = []

            if self.CSVHeader:
                try:
                    self.CSVData = pd.read_csv(self.DataSourcePath)
                except UnicodeDecodeError:
                    self.CSVData = pd.read_csv(self.DataSourcePath, engine = 'python')
                self.CSVHeaderLabel = self.CSVData.columns.tolist()

            else:
                try:
                    self.CSVData = pd.read_csv(self.DataSourcePath, header=None)
                except UnicodeDecodeError:
                    self.CSVData = pd.read_csv(self.DataSourcePath, header=None, engine = 'python')

                for i in range(len(self.CSVData.columns)):
                    self.CSVHeaderLabel.append("Column " + str(i + 1))

                self.CSVData.columns = self.CSVHeaderLabel

            for col in range(len(self.CSVData.columns)):
                try:
                    if not self.CSVData.iloc[:, col].dtype == np.float64 and not self.CSVData.iloc[:, col].dtype == np.int64:
                        self.CSVData.iloc[:, col] = pd.to_datetime(self.CSVData.iloc[:, col])
                except:
                    pass


            self.DataSourceLoadError = False
            self.DataSourceHTTPError = False

        except urllib.error.HTTPError:
            self.DataSourceHTTPError = True
            self.DataSourceLoadError = False

        except Exception as e:
            self.DataSourceHTTPError = False
            self.DataSourceLoadError = True

        if not self.DataSourceLoadError and self.CSVPathFlag:
            st = os.stat(self.DataSourcePath)
            self.DataSourceSize = st[ST_SIZE]
            self.DataSourceAccessTime = time.asctime(time.localtime(st[ST_ATIME]))
            self.DataSourceModifiedTime = time.asctime(time.localtime(st[ST_MTIME]))
            self.DataSourceChangeTime = time.asctime(time.localtime(st[ST_CTIME]))

    # Web URL
    def WebDataSource(self):
        try:
            response = requests.get(self.DataSourcePath)
            self.DataSourceLoadError = False
            try:
                response.raise_for_status()
            except requests.exceptions.HTTPError as e:
                self.DataSourceLoadError = True
                self.DataSourceURLHTTPError = True
                self.DataSoureURLErrorMessage = str(e)

        except requests.exceptions.ConnectionError as e:
            self.DataSourceLoadError = True
            self.DataSourceURLConnectionError = True
            self.DataSoureURLErrorMessage = str(e)

        except requests.exceptions.MissingSchema as e:
            self.DataSourceLoadError = True
            self.DataSourceURLMissingSchema = True
            self.DataSoureURLErrorMessage = str(e)

        if not self.DataSourceLoadError:
            self.DataSourceForbiddenLoadError = False
            try:
                self.DataSourceHTML = urllib.request.urlopen(self.DataSourcePath).read()
            except urllib.error.HTTPError as e:
                self.DataSourceForbiddenLoadError = True

            if not self.DataSourceForbiddenLoadError:
                try:
                    soup = BeautifulSoup(self.DataSourceHTML, features="lxml")
                except:
                    soup = BeautifulSoup(self.DataSourceHTML)

                # kill all script and style elements
                for script in soup(["script", "style"]):
                    script.extract()  # rip it out

                # get text
                text = soup.get_text()

                # break into lines and remove leading and trailing space on each
                lines = (line.strip() for line in text.splitlines())
                # break multi-headlines into a line each
                chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
                # drop blank lines
                text = '\n'.join(chunk for chunk in chunks if chunk)

                self.DataSourcetext = text

    # Twitter Tweet
    def TweetDataSource(self, Hashtag, Since, NoOfTweet):
        try:
            self.DataSourceHashtag = Hashtag

            consumer_key = 'Xucgf7aPmJYsBA0K98M0YFxAc'
            consumer_secret = 'PMKuIKlPWLJOeYkwi8aPlaX0Riffp9L9HlDBE7DArNaSeazJ0P'
            access_token = '1115595365380550659-w98KBQOKYclQ6hr1ojHZTVBAeqc7sZ'
            access_token_secret = 'n519RwjNgOBT7wWqCsNgcGgc9P2ky4ZbfiGn1n7TgErBg'

            auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
            auth.set_access_token(access_token, access_token_secret)
            api = tweepy.API(auth, wait_on_rate_limit=True)

            self.TweetData = []

            tweetdata = tweepy.Cursor(api.search, q=Hashtag, count=NoOfTweet, lang="en", since=Since).items()

            for tweet in tweetdata:
                eachtweet = [tweet.user.screen_name,
                             tweet.user.name,
                             str(tweet.created_at),
                             tweet.text,
                             str(tweet.user.location),
                             str(tweet.coordinates),
                             str(tweet.retweet_count),
                             str(tweet.retweeted),
                             str(tweet.source),
                             str(tweet.favorite_count),
                             str(tweet.favorited),
                             str(tweet.in_reply_to_status_id_str)]

                self.TweetData.append(eachtweet)

            if len(self.TweetData) == 0:
                self.DataSourceRetrieveZeroError = True
            else:
                # Converting Tweet Data to Pandas DataFrame
                self.TweetDataFrame = pd.DataFrame(self.TweetData)
                self.TweetDataFrame.columns = ["Screen Name", "User Name", "Tweet Created At", "Tweet Text", "User Location", "Tweet Coordinates",
                 "Retweet Count", "Retweeted", "Phone Type", "Favorite Count", "Favorited", "Replied"]

                for col in self.TweetDataFrame.columns:
                    try:
                        self.TweetDataFrame[col] = pd.to_numeric(self.TweetDataFrame[col])
                    except:
                        try:
                            self.TweetDataFrame[col] = pd.to_datetime(self.TweetDataFrame[col])
                        except:
                            pass

                filehandler = open("List2", 'wb')
                pickle.dump(self.TweetDataFrame, filehandler)

                self.DataSourceRetrieveZeroError = False

        except Exception as e:
            self.DataSourceLoadError = True

    #Yotube Comments From URL
    def YoutubeURL(self):
        self.YoutubeURLFlag = True

        Youtube_API_Key = 'Enter Your API Key'

        try:
            video_id = urlparse(self.DataSourcePath)
            q = parse_qs(video_id.query)
            vid = q["v"][0]

            VC = VideoComment(100, vid, Youtube_API_Key)
            self.YoutubeData = VC.comments

            self.DataSourcetext = ""
            for row in range(len(self.YoutubeData)):
                self.DataSourcetext = self.DataSourcetext + self.YoutubeData[row][0]

            self.DataSourceLoadError = False
        except Exception as e:
            self.DataSourceLoadError = True

    # Yotube Comments From KeyWord
    def YoutubeKeyWord(self):
        if not YoutubeServerNotFoundError:
            self.YoutubeServerNotFoundError = False
            self.YoutubeKeyWordFlag = True
            try:
                self.YoutubeData = retreiveComments(self.DataSourcePath)

                self.DataSourcetext = ""
                for row in range(len(self.YoutubeData)):
                    self.DataSourcetext = self.DataSourcetext + self.YoutubeData[row][4]
                self.DataSourceLoadError = False

            except Exception as e:
                print(str(e))
                self.DataSourceLoadError = True
        else:
            self.YoutubeServerNotFoundError = True

    # Summary
    def Summarize(self, Default, Criteria, Value):
        if Default:
            self.DataSourceTextSummary = summarization.summarizer.summarize(self.DataSourcetext)
        else:
            if Criteria == "Ratio":
                self.DataSourceTextSummary = summarization.summarizer.summarize(self.DataSourcetext, ratio=Value)
            elif Criteria == "Total Word Count":
                self.DataSourceTextSummary = summarization.summarizer.summarize(self.DataSourcetext, word_count=Value)

    #detection
    def detect(self):
        self.LanguageDetectionError = False

        blob = TextBlob(self.DataSourcetext)
        try:
            self.OriginalText = blob.detect_language()
        except:
            self.LanguageDetectionError = True

    #translation
    def translate(self, TranslateTo):
        self.TranslationError = False
        blob = TextBlob(self.DataSourcetext)
        try:
            self.DataSourceTranslatedText = blob.translate(to=TranslateTo)
            self.isTranslated = True
        except Exception as e:
            self.TranslationError = True

    # Create Case
    def CreateCase(self, CaseTopic, selectedText):
        self.CasesList.append(Cases(CaseTopic, len(self.DataSourcetext)))
        self.AddtoCase(CaseTopic, selectedText)

    # Add to Case
    def AddtoCase(self, CaseTopic, SelectedText):
        for cases in self.CasesList:
            if cases.CaseTopic == CaseTopic:
                cases.addtoCase(SelectedText)
                break

    # Create Sentiments
    def CreatSentiments(self):
        self.SentimentList.append(Sentiments("Good"))
        self.SentimentList.append(Sentiments("Neutral"))
        self.SentimentList.append(Sentiments("Bad"))

    # Automatic Sentiment Analysis
    def SentimentAnalysis(self, ColumnName):
        DataSourceTextTokenize = []
        if self.DataSourceext == "Youtube":
            for Comment in self.YoutubeData:
                Temp = self.deEmojify(self.tweet_cleaner(Comment[0]))
                if len(Temp) > 0:
                    DataSourceTextTokenize.append(Temp)

        elif self.DataSourceext == "Tweet":
            for Tweet in self.TweetData:
                Temp = self.deEmojify(self.tweet_cleaner(Tweet[3]))
                if len(Temp) > 0:
                    DataSourceTextTokenize.append(Temp)

        elif self.DataSourceext == "CSV files (*.csv)":
            for Header in self.CSVHeaderLabel:
                if Header == ColumnName:
                    index = self.CSVHeaderLabel.index(Header)
                    break

            for i in range(len(self.CSVData.index)):
                Temp = self.deEmojify(self.tweet_cleaner(str(self.CSVData.iloc[i, index])))
                if len(Temp) > 0:
                    DataSourceTextTokenize.append(Temp)


        self.PositiveSentimentCount = 0
        self.NegativeSentimentCount = 0
        self.NeutralSentimentCount = 0

        for line in DataSourceTextTokenize:
            if str(line) != 'nan':
                blob = TextBlob(line)
                polarity_score = blob.sentiment.polarity

                if polarity_score > 0.02:
                    self.AutomaticSentimentList.append([line, 'Positive'])
                    self.PositiveSentimentCount += 1

                elif polarity_score < -0.02:
                    self.AutomaticSentimentList.append([line, 'Negative'])
                    self.NegativeSentimentCount += 1

                else:
                    self.AutomaticSentimentList.append([line, 'Neutral'])
                    self.NeutralSentimentCount += 1

    # Tweet Cleaner
    def tweet_cleaner(self, text):
        text = re.sub(r'https?://[A-Za-z0-9./]+', '', text)
        text = "".join([char for char in text if char not in string.punctuation])
        text = re.sub('[0-9]+', '', text)
        return text

    # Emoji Cleaner
    def deEmojify(self, inputString):
        return inputString.encode('ascii', 'ignore').decode('ascii')

    # Word Tree
    def CreateWordTree(self, width, height):
        CleanDataSourceText = self.DataSourcetext.replace('\n', ' ').replace('\r', '')
        CleanDataSourceText = CleanDataSourceText.lower()

        tokenize = sent_tokenize(CleanDataSourceText)

        word = self.FindWordWithMaxFrequency()

        tokenizeList = []
        for token in tokenize:
            if word in token:# or LemWord in token or StemWord in token:
                tokenizeList.append(token)

        HTMLData = "[['Phrases'], "
        for items in tokenizeList:
            HTMLData = HTMLData + "['" + items + "'], "

        HTMLData = HTMLData + "]"

        EntityHTML = '''
                     <html>
                          <head>
                            <script type="text/javascript" src="https://www.gstatic.com/charts/loader.js"></script>
                            <script type="text/javascript">
                              google.charts.load('current', {packages:['wordtree']});
                              google.charts.setOnLoadCallback(drawChart);

                              function drawChart() {
                                var data = google.visualization.arrayToDataTable(
                     '''

        EntityHTML = EntityHTML + HTMLData
        EntityHTML = EntityHTML + '''
                                            );

                                            var options = {
                                              wordtree: {
                                                format: 'implicit',
                                                word: 
                                   '''
        EntityHTML = EntityHTML + "'" + word + "'"
        EntityHTML = EntityHTML +     '''         
                                            ,
                                                type: 'double',
                                              }
                                            };

                                            var chart = new google.visualization.WordTree(document.getElementById('wordtree_basic'));
                                            chart.draw(data, options);
                                          }
                                        </script>
                                      </head>
                                      <body>
                                        <div id="wordtree_basic" style="width:''' + str(width) + '''px; height: "''' + str(height) + '''px;"></div>
                                      </body>
                                 </html>   
                                 '''
        return EntityHTML

    # Find Word with Maximum Frequency
    def FindWordWithMaxFrequency(self):
        # convert all text to lowercase
        doc_text = self.DataSourcetext.lower()

        # remove numbers
        doc_text = re.sub(r'\d+', '', doc_text)

        # remove punctuation, characters and whitespaces
        doc_text = re.sub('\W+', ' ', doc_text)

        # remove stopwords and tokenize
        stop_words = set(stopwords.words('english'))
        tokens = word_tokenize(doc_text)
        result = [i for i in tokens if not i in stop_words]

        wordlist = []

        for word in result:
            if len(word) > 2:
                wordlist.append(word)

        wordfreq = []
        for w in wordlist:
            wordfreq.append(wordlist.count(w))

        return max(list(zip(wordlist, wordfreq)), key=itemgetter(1))[0]

    # Sentiment Analsysis Visuals
    def SentimentAnalysisVisualization(self):
        # Pie Chart
        self.PieSentimentFigure = plt.figure(figsize=(10, 5))
        ax1 = self.PieSentimentFigure.add_subplot(111)

        # Data to plot
        labels = 'Positive', 'Negative', 'Neutral'
        sizes = [self.PositiveSentimentCount, self.NegativeSentimentCount, self.NeutralSentimentCount]
        colors = ['lightgreen', 'lightcoral', 'yellow']
        explode = (0, 0, 0)  # explode 1st slice

        # Plot
        ax1.pie(sizes, explode=explode, labels=labels, colors=colors,
                autopct='%1.1f%%', shadow=True, startangle=140)

        ax1.legend(labels, loc="upper left")
        ax1.axis('equal')

        # data = {
        #     "Positive": (self.PositiveSentimentCount, QColor("green")),
        #     "Neutral": (self.NeutralSentimentCount, QColor("yellow")),
        #     "Negative": (self.NegativeSentimentCount, QColor("red")),
        # }
        #
        # series = QPieSeries()
        #
        # series.setLabelsVisible(True)
        # series.setLabelsPosition(QPieSlice.LabelInsideHorizontal)
        # series.setLabelsVisible(True)
        #
        # _sliceList = []
        #
        # for name, (value, color) in data.items():
        #     _slice = series.append(name, value)
        #     _slice.setBrush(color)
        #     _slice.setLabelVisible(False)
        #     _slice.setLabelPosition(QPieSlice.LabelInsideHorizontal)
        #     _slice.setLabelFont(QFont("Times", 8, QFont.Bold))
        #     _sliceList.append(_slice)
        #
        # for _slice in _sliceList:
        #     _slice.setLabel(_slice.label() + " " + str(round(100 * _slice.percentage(), 2)) + "%")
        #
        # chart = QChart()
        # chart.setAnimationOptions(QChart.AllAnimations)
        #
        # # chart.setTheme(QChart.ChartThemeBlueNcs)
        # # chart.setTheme(QChart.ChartThemeHighContrast)
        # # chart.setTheme(QChart.ChartThemeBlueIcy)
        # chart.setTheme(QChart.ChartThemeQt)
        #
        # chart.addSeries(series)
        #
        # chart.legend().setVisible(True)
        # chart.legend().setAlignment(Qt.AlignRight)
        # chart.legend().setFont(QFont("Times", 10))
        #
        # self.chartview = QChartView(chart)
        # self.chartview.setRenderHint(QPainter.Antialiasing)

        # Bar Chart
        self.BarSentimentFigure = plt.figure(figsize=(10, 5))
        ax2 = self.BarSentimentFigure.add_subplot(111)

        objects = ('Positive', 'Negative', 'Neutral')
        y_pos = np.arange(len(objects))
        performance = [self.PositiveSentimentCount, self.NegativeSentimentCount, self.NeutralSentimentCount]
        colors = ['green', 'red', 'yellow']

        ax2.bar(y_pos, performance, align='center', alpha=0.5, color=colors)
        ax2.set_xticks(y_pos)
        ax2.set_xticklabels(objects)
        ax2.set_ylabel('Count')

    # Cases Coverage Graph
    def allCasesCoverage(self):
        # Bar Chart
        self.BarCasesCoverageFigure = plt.figure(figsize=(10, 5))
        ax2 = self.BarCasesCoverageFigure.add_subplot(111)

        objects = []
        performance = []
        for cases in self.CasesList:
            if not cases.MergedCase:
                totalweightage = 0
                for casetext in cases.TopicCases:
                    totalweightage += casetext[3]
                objects.append(cases.CaseTopic)
                performance.append(totalweightage)
            # else:
            #     totalweightage = 0
            #     for cases2 in self.CasesList:
            #         if cases == cases2.ParentCase:
            #             for casetext in cases2.TopicCases:
            #                 totalweightage += casetext[3]
            #     objects.append(cases.CaseTopic)
            #     performance.append(totalweightage)

        y_pos = np.arange(len(objects))
        ax2.bar(y_pos, performance, align='center', alpha=0.5, color=np.random.rand(len(objects), 3))
        ax2.set_xticks(y_pos)
        ax2.set_xticklabels(tuple(objects))
        ax2.set_ylabel('Case Weigthage')

