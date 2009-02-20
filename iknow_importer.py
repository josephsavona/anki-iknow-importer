from iknow import IknowCache

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ankiqt import mw
from ankiqt.ui.utils import getOnlyText
from anki.models import Model, FieldModel, CardModel
from anki.facts import Field

import re, urllib

VOCAB_MODEL_NAME = u"iKnow! Vocabulary"
SENTENCE_MODEL_NAME = u"iKnow! Sentences"
IMPORT_AUDIO = True

#def doModelsExist():
#    vocab = False
#    sent = False
#    for m in mw.deck.models:
#        if m.name.lower() == VOCAB_MODEL_NAME.lower():
#            vocab = True
#        elif m.name.lower() == SENTENCE_MODEL_NAME.lower():
#            sent = True
#    if vocab and sent:
#        return True
#    return False

def makeModelsNow():
    ensureSentenceModelExists()
    ensureVocabModelExists()
    QMessageBox.information(mw,"Information","Models created. You may want to customize them now before you import.\n\nDo *not* delete/rename the models themselves or any of the fields.\n\n You may, however:\n* delete card types\n* add new card types\n* change the format of the card types.")
    
def doModelsExist():
    (s, v) = getModels()
    if s and v:
        return True
    else:
        return False
    
def getModels():
    return (findModel(SENTENCE_MODEL_NAME), findModel(VOCAB_MODEL_NAME))

def findModel(name):
    for m in mw.deck.models:
        if m.name.lower() == name.lower():
            return m
    return None

def ensureModelExists(name, production, reading, listening):
    model = None
    for m in mw.deck.models:
        if m.name.lower() == name.lower():
            return m
    if not model:
        model = Model(name)
        model.addFieldModel(FieldModel(u'Expression', True, False))
        model.addFieldModel(FieldModel(u'Meaning', True, False))
        model.addFieldModel(FieldModel(u'Reading', False, False))
        model.addFieldModel(FieldModel(u'Audio', False, False))
        model.addFieldModel(FieldModel(u'Image_URI', False, False))
        model.addFieldModel(FieldModel(u'iKnowID', True, True))
        model.addFieldModel(FieldModel(u'iKnowType', False, False))
        if listening:
            model.addCardModel(CardModel(
                u'Listening',
                u'Listen.%(Audio)s',
                u'%(Expression)s<br>%(Reading)s<br>%(Meaning)s'))
        if production:
            model.addCardModel(CardModel(
                u'Production',
                u'%(Meaning)s<br>%(Image_URI)s',
                u'%(Expression)s<br>%(Reading)s<br>%(Audio)s'))
        if reading:
            model.addCardModel(CardModel(
                u'Reading',
                u'%(Expression)s',
                u'%(Reading)s<br>%(Meaning)s<br>%(Audio)s'))
        mw.deck.addModel(model)
    return model

def ensureVocabModelExists(production=True, reading=True, listening=True):
    return ensureModelExists(VOCAB_MODEL_NAME, production, reading, listening)

def ensureSentenceModelExists(production=True, reading=True, listening=True):
    return ensureModelExists(SENTENCE_MODEL_NAME, production, reading, listening)
        
def importIknowItem(item, sentenceModel, vocabModel, readingType=None):
    query = mw.deck.s.query(Field).filter_by(value=item["iknow_id"])
    field = query.first()
    if field:
        return False#is duplicate, so return immediately
    
    if item["type"] == "item":
        model = vocabModel
    elif item["type"] == "sentence":
        model = sentenceModel
    fact = mw.deck.newFact(model)
    fact['iKnowID'] = item["iknow_id"]
    fact['Expression'] = item["expression"]
    fact['Meaning'] = item["meaning"]
    fact['iKnowType'] = item["type"]
    if readingType and "reading@%s" % readingType.lower() in item:
        fact['Reading'] = item["reading@%s" % readingType.lower()]
    else:
        if item["language"] == "ja" and "reading@hrkt" in item:
            fact['Reading'] = item["reading@hrkt"]
        elif "reading@latn" in item:
            fact['Reading'] = item["reading@latn"]
        else:
            fact['Reading'] = u""
    if "image_uri" in item:
        fact['Image_URI'] = u'<img src="%s" alt="[No Image]" />' % item["image_uri"]
    else:
        fact['Image_URI'] = u""
    if IMPORT_AUDIO and "audio_uri" in item:
        (filePath, headers) = urllib.urlretrieve(item["audio_uri"])
        path = mw.deck.addMedia(filePath)
        fact['Audio'] = u"[sound:%s]" % path
    else:
        item["audio_uri"] = u""
    mw.deck.addFact(fact)
    mw.deck.save()
    return True

def getCachedImportConfirm():
    if 'iknow.confirmBeforeEachImport' in mw.config and len(mw.config['iknow.confirmBeforeEachImport']) > 0:
        return mw.config['iknow.confirmBeforeEachImport']
    else:
        return None

def forcegetImportConfirm():
    importConfirm = getOnlyText("Enter the types of items to confirm with space(s) between them. Options are 'item' and/or 'sentence'").lower().strip()
    if len(importConfirm) > 0:
        mw.config['iknow.confirmBeforeEachImport'] = importConfirm
        return importConfirm
    else:
        del mw.config['iknow.confirmBeforeEachImport']
        return None

def getUsername():
    if "iknow.username" in mw.config and len(mw.config['iknow.username']) > 0:
        return mw.config["iknow.username"]
    else:
        haveName = False
        while not haveName:
            username = getOnlyText("Enter your iKnow! username:").strip()
            if len(username) == 0:
                continue
            mw.config["iknow.username"] = username
            return username

def clearUserPreferences():
    if "iknow.username" in mw.config:
        del mw.config["iknow.username"]
    if "iknow.nativeLangCode" in mw.config:
        del mw.config["iknow.nativeLangCode"]
    if "iknow.confirmBeforeEachImport" in mw.config:
        del mw.config["iknow.confirmBeforeEachImport"]
   
def resetUserPrefs():
    mw.config["iknow.username"] = u""
    mw.config["iknow.nativeLangCode"] = u""
    mw.config["iknow.confirmBeforeEachImport"] = u""
    username = getUsername()
    nativeLangCode = getNativeLangCode()
    importConfirm = forcegetImportConfirm() or u""
    QMessageBox.information(mw,"Information", "Preferences set.\nUsername = '%s'\nnative language code = '%s'\nconfirming imports for types '%s'" % (username, nativeLangCode, importConfirm))

def getStudyingLangCode():
    haveCode = False
    while not haveCode:
        code = getOnlyText("Enter the code for the language you want to study - 'en' English, 'ja' Japanese, 'zh-CN' Chinese, etc:").strip()
        if len(code) == 0:
            continue
        return code

def getNativeLangCode():
    if "iknow.nativeLangCode" in mw.config and len(mw.config['iknow.nativeLangCode']) > 0:
        return mw.config["iknow.nativeLangCode"]
    else:
        haveCode = False
        while not haveCode:
            nativeLangCode = getOnlyText("Enter the code for your **native** language. For an English speaker learning Japanese, you'd enter 'en'.\n\nCommon languages are: 'en' English,\n'ja' Japanese,\n'zh-CN' Chinese").strip()
            if len(nativeLangCode) == 0:
                continue
            mw.config["iknow.nativeLangCode"] = nativeLangCode
            return nativeLangCode

def getListId():
    haveId = False
    while not haveId:
        url = getOnlyText("Enter the URL of an iKnow list:").strip()
        if not url or len(url) == 0:
            continue
        listId = re.search("lists/(\d+)", url)
        if not listId:
            QMessageBox.warning(mw,"Warning", "Please enter a valid iKnow list URL. Example: http://www.iknow.co.jp/lists/19053-Japanese-Core-2000-Step-1")
            continue
        return listId.group(1)

class ProgressTracker:
    def __init__(self, log=None):
        self.dialog = QProgressDialog(_("Importing..."), "", 0, 0, mw)
        self.dialog.setCancelButton(None)
        self.dialog.setMaximum(100)
        self.dialog.setMinimumDuration(0)
        self.dialog.setLabelText("Starting import..")
        self.currentPercent = 0
        if log:
            self.logFile = open(log, 'a')
            self.logFile.write("START [")
        else:
            self.logFile = None
    
    def close(self):
        if self.logFile:
            self.logFile.write("] END")
            self.logFile.flush()
            self.logFile.close()
    
    def logMsg(self, msg):
        if self.logFile:
            self.logFile.write(str(msg))
            self.logFile.flush()
    
    def downloadCallback(self, url, pageNumber, itemCount):
        self.currentPercent += 1
        self.logMsg("url:%s\npage#:%s\nitems:%s\n\n" % (url, pageNumber, itemCount))
        self.dialog.setLabelText("Downloading page %s, got %s items so far." % (pageNumber, itemCount))
        self.dialog.setValue(self.currentPercent)
        mw.app.processEvents()
    
    def preImportResetProgress(self, count):
        self.currentPercent = 0
        self.dialog.setMaximum(count)
        self.dialog.setMinimumDuration(0)
        self.dialog.setValue(0)
        self.dialog.setLabelText("Starting to import %s items" % count)
        self.logMsg("starting to import %s items\n\n" % count)
        mw.app.processEvents()
    
    def importCallback(self, processedCount, currentItem):
        self.dialog.setValue(processedCount)
        self.dialog.setLabelText("Importing %s" % currentItem)
        mw.app.processEvents()

def preFetch():
    models = getModels()
    progress = ProgressTracker("/tmp/iknowAnkiPluginLog.txt")
    iknow = IknowCache(getUsername(), getNativeLangCode(), ":memory:")
    iknow.setCallback(progress.downloadCallback)
    return (progress, iknow, models)

def postFetch(progress, items, models, sentencesOnly):
    (sentenceModel, vocabModel) = models
    progress.preImportResetProgress(len(items))
    totalImported = 0
    totalDup = 0
    confirmTypes = getCachedImportConfirm()
    for i, item in enumerate(items):
        progress.importCallback(i, item["expression"])
        if sentencesOnly and item["type"] != "sentence":
            continue
        if confirmTypes and confirmTypes.find(item["type"]) >= 0:
            if not confirmImportOfItem(item):
                continue
        if importIknowItem(item, sentenceModel, vocabModel):
            totalImported += 1
        else:
            totalDup += 1
    progress.dialog.cancel()
    progress.close()
    mw.deck.save()
    mw.reset()
    QMessageBox.information(mw,"Summary","Import complete. Imported %s items and skipped %s duplicates." % (totalImported, totalDup))

def confirmImportOfItem(item):
    yesImport = getOnlyText("About to import:\nExpression: %s\nMeaning: %s\n\nEnter any text to import, leave blank to skip:" % (item["expression"], item["meaning"]))
    if len(yesImport) > 0:
        return True
    else:
        return False

def importList(sentencesOnly=False):
    if not doModelsExist():
        QMessageBox.warning(mw, "Warning", "This is your first import. New models will be created for vocabulary and sentences - please edit the card types for these models to suit your needs, and then try importing again.")
        makeModelsNow()
        return
    (progress, iknow, models) = preFetch()
    listId = getListId()
    items = list()
    try:
        items = iknow.listItems(listId, True)
    except:
        progress.dialog.cancel()
        QMessageBox.warning(mw,"Warning","There was a problem retrieving data from iKnow!. Please check your internet connection and ensure you can reach http://api.iknow.co.jp.")
        mw.deck.save()
        mw.reset()
    else:
        postFetch(progress, items, models, sentencesOnly)

def importListSentencesOnly():
    importList(True)

def importUserItems(sentencesOnly=False):
    if not doModelsExist():
        QMessageBox.warning(mw, "Warning", "This is your first import. New models will be created for vocabulary and sentences - please edit the card types for these models to suit your needs, and then try importing again.")
        makeModelsNow()
        return
    (progress, iknow, models) = preFetch()
    items = list()
    try:
        items = iknow.userItems(True, getStudyingLangCode())
    except:
        progress.dialog.cancel()
        QMessageBox.warning(mw,"Warning","There was a problem retrieving data from iKnow!. Please check your internet connection and ensure you can reach http://api.iknow.co.jp.")
        mw.deck.save()
        mw.reset()
    else:
        postFetch(progress, items, models, sentencesOnly)

def importUserItemsSentencesOnly():
    importUserItems(True)

userAll = QAction(mw)
userAll.setText("iKnow - User Vocab and Sentences")
mw.connect(userAll, SIGNAL("triggered()"),
    importUserItems)

userSent = QAction(mw)
userSent.setText("iKnow - User Sentences")
mw.connect(userSent, SIGNAL("triggered()"),
    importUserItemsSentencesOnly)

listAll = QAction(mw)
listAll.setText("iKnow - List Vocab and Sentences")
mw.connect(listAll, SIGNAL("triggered()"),
    importList)

listSent = QAction(mw)
listSent.setText("iKnow - List Sentences")
mw.connect(listSent, SIGNAL("triggered()"),
    importListSentencesOnly)
    
resetPrefs = QAction(mw)
resetPrefs.setText("iKnow - Reset Username and Language")
mw.connect(resetPrefs, SIGNAL("triggered()"),
    resetUserPrefs)
    
clearPrefs = QAction(mw)
clearPrefs.setText("iKnow - Clear Preferences")
mw.connect(clearPrefs, SIGNAL("triggered()"),
    clearUserPreferences)

mw.mainWin.menuTools.addSeparator()
mw.mainWin.menuTools.addAction(userAll)
mw.mainWin.menuTools.addAction(userSent)
mw.mainWin.menuTools.addAction(listAll)
mw.mainWin.menuTools.addAction(listSent)
mw.mainWin.menuTools.addSeparator()
mw.mainWin.menuTools.addAction(resetPrefs)
mw.mainWin.menuTools.addAction(clearPrefs)

#if not doModelsExist():
setMods = QAction(mw)
setMods.setText("iKnow - Customize Card Models")
mw.connect(setMods, SIGNAL("triggered()"),
    makeModelsNow)
mw.mainWin.menuTools.addAction(setMods)