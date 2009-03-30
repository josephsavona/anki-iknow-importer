from PyQt4.QtCore import SIGNAL
from PyQt4.QtGui import QAction, QMessageBox
from PyQt4 import QtCore, QtGui
from ankiqt import mw
from ankiqt.ui.utils import getOnlyText
from anki.models import Model, FieldModel, CardModel
from anki.facts import Field
import os, re, time, urllib, traceback
from iknow import SmartFMCache, SmartFMDownloadError


class AudioDownloadError(Exception):
    pass

class SmartFMModelCustomizeDialog(QtGui.QDialog):
    def __init__(self, cardSettings, showVocab, showSentence):
        QtGui.QDialog.__init__(self)
        self.cardSettings = cardSettings
        self.showSentence = showSentence
        self.showVocab = showVocab
        self.setObjectName("smartfmCardCustomizeDialog")
        self.setWindowTitle("Smart.fm - Customize Card Types")
        self.resize(450, 600)
        
        self.mainLayout = QtGui.QVBoxLayout(self)
        self.mainLayout.setSpacing(6)
        self.mainLayout.setMargin(9)
        self.mainLayout.setObjectName("mainLayout")
        
        if self.showVocab:
            self.labelVocab = QtGui.QLabel("Vocabulary Model - Card Types")
            self.labelVocab.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
            self.labelVocab.setWordWrap(True)
            self.mainLayout.addWidget(self.labelVocab)
        
            self.checkProduction = QtGui.QCheckBox("Production card (from your native language to a new language)")
            self.checkProduction.setChecked(self.cardSettings.vocabProduction)
            self.mainLayout.addWidget(self.checkProduction)
        
            self.checkListening = QtGui.QCheckBox("Listening card (hear the word and remember its meaning)")
            self.checkListening.setChecked(self.cardSettings.vocabListening)
            self.mainLayout.addWidget(self.checkListening)
        
            self.checkReading = QtGui.QCheckBox("Reading card (read the word and remember its meaning)")
            self.checkReading.setChecked(self.cardSettings.vocabReading)
            self.mainLayout.addWidget(self.checkReading)
        
        if self.showSentence:
            self.labelSentences = QtGui.QLabel("Sentences Model - Card Types")
            self.labelSentences.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
            self.labelSentences.setWordWrap(True)
            self.mainLayout.addWidget(self.labelSentences)
        
            self.checkProductionSentences = QtGui.QCheckBox("Production card (from your native language to a new language)")
            self.checkProductionSentences.setChecked(self.cardSettings.sentenceProduction)
            self.mainLayout.addWidget(self.checkProductionSentences)
        
            self.checkListeningSentences = QtGui.QCheckBox("Listening card (hear the word and remember its meaning)")
            self.checkListeningSentences.setChecked(self.cardSettings.sentenceListening)
            self.mainLayout.addWidget(self.checkListeningSentences)
        
            self.checkReadingSentences = QtGui.QCheckBox("Reading card (read the word and remember its meaning)")
            self.checkReadingSentences.setChecked(self.cardSettings.sentenceReading)
            self.mainLayout.addWidget(self.checkReadingSentences)
        
        self.btnSubmit = QtGui.QPushButton(self)
        self.btnSubmit.setText("Start Import")
        self.mainLayout.addWidget(self.btnSubmit)
        
        self.btnCancel = QtGui.QPushButton(self)
        self.btnCancel.setText("Cancel")
        self.mainLayout.addWidget(self.btnCancel)
        
        self.connect(self.btnSubmit, QtCore.SIGNAL("clicked()"), self.submitClicked)
        self.connect(self.btnCancel, QtCore.SIGNAL("clicked()"), self.reject)
        
    def submitClicked(self):
        self.btnSubmit.setEnabled(False)
        if self.showVocab:
            self.cardSettings.vocabProduction = self.checkProduction.isChecked()
            self.cardSettings.vocabListening = self.checkListening.isChecked()
            self.cardSettings.vocabReading = self.checkReading.isChecked()
        if self.showSentence:
            self.cardSettings.sentenceProduction = self.checkProductionSentences.isChecked()
            self.cardSettings.sentenceListening = self.checkListeningSentences.isChecked()
            self.cardSettings.sentenceReading = self.checkReadingSentences.isChecked()
        self.accept()


class IknowImportDialog(QtGui.QDialog):
    def __init__(self, importSettings):
        QtGui.QDialog.__init__(self)
        self.importSettings = importSettings
        self.setObjectName("Smart.fm Import")
        self.setWindowTitle("Smart.fm Import")
        self.resize(450, 600)
    
        self.mainLayout = QtGui.QVBoxLayout(self)
        self.mainLayout.setSpacing(6)
        self.mainLayout.setMargin(9)
        self.mainLayout.setObjectName("mainLayout")
    
        self.settingsBox = QtGui.QGroupBox("Import Settings", self)
        self.settingsLayout = QtGui.QVBoxLayout(self.settingsBox)
        self.mainLayout.addWidget(self.settingsBox)
        
        self.labelSource = QtGui.QLabel("URL of the smart.fm list you wish to import. Example: http://smart.fm/lists/35430-chinese-media-lesson-1")
        self.labelSource.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.labelSource.setWordWrap(True)
        self.settingsLayout.addWidget(self.labelSource)
        self.txt_source = QtGui.QLineEdit(self)
        self.txt_source.setMaxLength(500)
        self.settingsLayout.addWidget(self.txt_source)
    
        self.rbtn_group_typesToImport = QtGui.QGroupBox("Item types to import:", self)
        self.rbtnLayout = QtGui.QVBoxLayout(self.rbtn_group_typesToImport)
        self.rbtn_typesToImportVocab = QtGui.QRadioButton("&Vocabulary", self.rbtn_group_typesToImport)
        self.rbtnLayout.addWidget(self.rbtn_typesToImportVocab)
        self.rbtn_typesToImportSent = QtGui.QRadioButton("&Sentences", self.rbtn_group_typesToImport)
        self.rbtnLayout.addWidget(self.rbtn_typesToImportSent)
        self.rbtn_typesToImportAll = QtGui.QRadioButton("&Both", self.rbtn_group_typesToImport)
        self.rbtnLayout.addWidget(self.rbtn_typesToImportAll)
        self.settingsLayout.addWidget(self.rbtn_group_typesToImport)
        
        self.labelAmount = QtGui.QLabel("Maximum number of items to import (leave blank to download all items):")
        self.labelAmount.setAlignment(QtCore.Qt.AlignLeading|QtCore.Qt.AlignLeft|QtCore.Qt.AlignTop)
        self.labelAmount.setWordWrap(True)
        self.settingsLayout.addWidget(self.labelAmount)
        self.txt_amountToImport = QtGui.QLineEdit(self)
        self.txt_amountToImport.setMaxLength(5)
        self.settingsLayout.addWidget(self.txt_amountToImport)
        
        self.check_AudioDownload = QtGui.QCheckBox("Download audio clips if available", self)
        self.check_AudioDownload.setChecked(self.importSettings.downloadAudio)
        self.settingsLayout.addWidget(self.check_AudioDownload)
        
        self.check_includeItemMeaning = QtGui.QCheckBox("Include keyword meanings with sentences")
        self.check_includeItemMeaning.setChecked(self.importSettings.includeItemMeaning)
        self.settingsLayout.addWidget(self.check_includeItemMeaning)
        
        self.check_boldKeywordMonolingual = QtGui.QCheckBox("Bold sentence keywords for monolingual lists")
        self.check_boldKeywordMonolingual.setChecked(self.importSettings.boldMonolingualKeywords)
        self.settingsLayout.addWidget(self.check_boldKeywordMonolingual)
        
        self.check_boldKeywordBilingual = QtGui.QCheckBox("Bold sentence keywords for bilingual lists")
        self.check_boldKeywordBilingual.setChecked(self.importSettings.boldBilingualKeywords)
        self.settingsLayout.addWidget(self.check_boldKeywordBilingual)
        
        self.btnStartImport = QtGui.QPushButton(self)
        self.btnStartImport.setText(_("Start Import"))
        self.btnStartImport.setDefault(True)
        self.mainLayout.addWidget(self.btnStartImport)
        
        self.importStatusLabel = QtGui.QLabel("")
        self.settingsLayout.addWidget(self.importStatusLabel)
    
        self.cancelButton = QtGui.QPushButton(self)
        self.cancelButton.setText(_("Finish"))
        self.mainLayout.addWidget(self.cancelButton)
        
        self.connect(self.btnStartImport, QtCore.SIGNAL("clicked()"), self.startImportClicked)
        self.connect(self.cancelButton, QtCore.SIGNAL("clicked()"), self.cancelClicked)
    
    def showErrors(self, errors):
        QMessageBox.warning(mw, "Warning", "There were various errors:%s" % "<br/>".join(errors))
        pass
    
    def clearErrors(self):
        pass 
    
    def startImportClicked(self):
        self.btnStartImport.setEnabled(False)
        self.clearErrors()
        errors = list()
        if self.rbtn_typesToImportAll.isChecked():
            self.importSettings.importSentences = True
            self.importSettings.importVocab = True
        elif self.rbtn_typesToImportSent.isChecked():
            self.importSettings.importSentences = True
        elif self.rbtn_typesToImportVocab.isChecked():
            self.importSettings.importVocab = True
        else:
            errors.append("Please choose a type of item to import")
        
        sourceText = self.txt_source.text()
        if sourceText:
            listId = re.search("lists/(\d+)", sourceText)
            if listId:
                self.importSettings.listId = unicode(listId.group(1))
            else:
                errors.append("URL of the smart.fm list is invalid, please see the example")
        else:
            errors.append("URL of the smart.fm list is required")
            
        maxItemsText = self.txt_amountToImport.text()
        if maxItemsText:
            if re.match("^\d+$", maxItemsText) and int(maxItemsText) >= 0:
                self.importSettings.maxItems = int(maxItemsText)
            else:
                errors.append("Maximum items to import must be all numeric, and greater than or equal to 0.")
        else:
            self.importSettings.maxItems = 0
        self.importSettings.downloadAudio = self.check_AudioDownload.isChecked()
        self.importSettings.includeItemMeaning = self.check_includeItemMeaning.isChecked()
        self.importSettings.boldBilingualKeywords = self.check_boldKeywordBilingual.isChecked()
        self.importSettings.boldMonolingualKeywords = self.check_boldKeywordMonolingual.isChecked()
        
        if len(errors) > 0:
            self.showErrors(errors)
            self.btnStartImport.setEnabled(True)
        else:
            self.accept()
    
    def cancelClicked(self):
        self.reject()


class SmartFMCardTypeSettings:
    def __init__(self):
        self.vocabProduction = False
        self.vocabListening = False
        self.vocabReading = True
        self.sentenceProduction = False
        self.sentenceListening = False
        self.sentenceReading = True


class SmartFMImportSettings:
    def __init__(self):
        self.listId = None
        self.maxItems = 0
        self.importVocab = False
        self.importSentences = False
        self.downloadAudio = True
        self.includeItemMeaning = True
        self.boldBilingualKeywords = False
        self.boldMonolingualKeywords = True


class SmartFMModelManager:
    VOCAB_MODEL_NAME = u"iKnow! Vocabulary"
    SENTENCE_MODEL_NAME = u"iKnow! Sentences"
    
    def __init__(self, importSettings):
        self.importSettings = importSettings
        self.loadModels()
    
    def loadModels(self):
        self.vocabModel = self.findModel(SmartFMModelManager.VOCAB_MODEL_NAME)
        self.sentenceModel = self.findModel(SmartFMModelManager.SENTENCE_MODEL_NAME)
        
    def findModel(self, modelName):
        for m in mw.deck.models:
            if m.name.lower() == modelName.lower():
                return m
        return None
    
    def isNeedsVocabModel(self):
        if self.importSettings.importVocab and not self.vocabModel:
            return True
        else:
            return False
    
    def isNeedsSentenceModel(self):
        if self.importSettings.importSentences and not self.sentenceModel:
            return True
        else:
            return False
    
    def createModelsFromSettings(self, cardSettings):
        if not self.vocabModel:
            self.createModel(SmartFMModelManager.VOCAB_MODEL_NAME, cardSettings.vocabProduction, cardSettings.vocabListening, cardSettings.vocabReading)
        if not self.sentenceModel:
            self.createModel(SmartFMModelManager.SENTENCE_MODEL_NAME, cardSettings.sentenceProduction, cardSettings.sentenceListening, cardSettings.sentenceReading)
        self.loadModels()
    
    def createModel(self, modelName, production, listening, reading):
        model = Model(modelName)
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


class ProgressTracker:
    def __init__(self, log=None):
        self.dialog = QtGui.QProgressDialog(_("Importing..."), "", 0, 0, mw)
        self.dialog.setCancelButton(None)
        self.dialog.setMaximum(0)
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



def formatIknowItemPreImport(item, importSettings):
    mainKeys = ["meaning", "expression", "reading"]
    hasOwnMeaning = True
    #store the reading
    if item["language"] == "ja" and "reading@hrkt" in item:
        item['reading'] = item["reading@hrkt"]
    elif "reading@latn" in item:
        item['reading'] = item["reading@latn"]
    else:
        item["reading"] = u""
        
    if 'meaning' not in item:
        hasOwnMeaning = False
        
    #for sentences in a monolingual list, use the item meaning 
    if 'meaning' not in item and 'item_meaning' in item:
        item['meaning'] = item['item_meaning']
    elif importSettings.includeItemMeaning and 'item_meaning' in item:
        #note this only applies when the sentence already has its own meaning and we are possibly adding to it
        item['meaning'] += u"<br />" + item['item_meaning']
        
    #if it has its own meaning (bilingual list) and we do NOT want bolding on bilingual lists, then remove the default bolding from smart.fm
    if hasOwnMeaning and not importSettings.boldBilingualKeywords:
        for key in mainKeys:
            item[key] = item[key].replace('<b>','').replace('</b>','')
    #if monolingual list, and we DO want bolding on monolingual lists, then bold the primary word if it isn't already bolded        
    if not hasOwnMeaning and importSettings.boldMonolingualKeywords and 'core_word' in item:
        for key in mainKeys:
            if item[key].find('<b>') >= 0:
                continue
            item[key] = item[key].replace(item['core_word'], u"<b>" + item['core_word'] + u"</b>")



def importIknowItem(item, sentenceModel, vocabModel, importSettings):
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
    fact['Reading'] = item["reading"]
    if "image_uri" in item:
        fact['Image_URI'] = u'<img src="%s" alt="[No Image]" />' % item["image_uri"]
    else:
        fact['Image_URI'] = u""
    if importSettings.downloadAudio and "audio_uri" in item:
        tries = 0
        gotAudioForItem = False
        while not gotAudioForItem and tries < 3:
            tries += 1
            try:
                (filePath, headers) = urllib.urlretrieve(item["audio_uri"])
                path = mw.deck.addMedia(filePath)
                fact['Audio'] = u"[sound:%s]" % path
                gotAudioForItem = True
            except:
                pass
        if not gotAudioForItem:
            raise AudioDownloadError, "Failed to get audio for an item after 3 tries, cancelling import. Error with URI %s" % item["audio_uri"]
    else:
        item["audio_uri"] = u""
    mw.deck.addFact(fact)
    mw.deck.save()
    return True



def runImport(modelManager, importSettings):
    try:
        progress = ProgressTracker(os.path.join(mw.pluginsFolder(), "iknow-smartfm-log.txt"))
        iknow = SmartFMCache(None, None, ":memory:")
        iknow.setCallback(progress.downloadCallback)
        items = iknow.listItems(importSettings.listId, importSettings.importSentences)
        progress.preImportResetProgress(len(items))
        totalImported = 0
        totalDup = 0
        totalImportedByType = {"item" : 0, "sentence" : 0}
        for i, item in enumerate(items):
            if importSettings.maxItems > 0 and totalImported >= importSettings.maxItems:
                break
            if not importSettings.importSentences and item["type"] == "sentence":
                continue
            if not importSettings.importVocab and item["type"] == "item":
                continue
            formatIknowItemPreImport(item, importSettings)
            progress.importCallback(i, item["expression"])
            if importIknowItem(item, modelManager.sentenceModel, modelManager.vocabModel, importSettings):
                totalImported += 1
                totalImportedByType[item["type"]] = totalImportedByType[item["type"]] + 1
            else:
                totalDup += 1
        progress.dialog.cancel()
        progress.close()
        mw.deck.save()
        mw.reset(mw.mainWin)
        QMessageBox.information(mw,"Summary","Import complete. Imported %s items, %s sentences, and skipped %s duplicates." % (totalImportedByType["item"], totalImportedByType["sentence"], totalDup))
    except AudioDownloadError:
        progress.logMsg(traceback.format_exc())
        progress.dialog.cancel()
        progress.close()
        QMessageBox.warning(mw, "Warning", "Data for one item could not be retrieved even after several retries. This is typically caused by smart.fm's (currently) slow servers. Please try your import again.")
        mw.reset(mw.mainWin)
    except SmartFMDownloadError:
        progress.logMsg(traceback.format_exc())
        progress.dialog.cancel()
        progress.close()
        QMessageBox.warning(mw,"Warning","There was a problem retrieving data from Smart.fm. Please check your internet connection and ensure you can reach http://api.smart.fm\n\nIf you are able to access smart.fm, please send the file 'iknow-smartfm-log.txt' (in the Anki plugins folder) to the plugin developer. See the IKNOW_IMPORT_README file for contact details.")
        mw.reset(mw.mainWin)
    except:
        progress.logMsg(traceback.format_exc())
        progress.dialog.cancel()
        progress.close()
        QMessageBox.warning(mw, "Warning", "There was an unknown error importing items. Please contact the plugin developer (see the IKNOW_IMPORT_READEM.txt file in your plugin folder for contact info).")
        mw.reset(mw.mainWin)



def runDialog():
    importSettings = SmartFMImportSettings()
    dialog = IknowImportDialog(importSettings)
    if dialog.exec_():
        QMessageBox.information(mw, "Information", "Got some import settings '%s' type '%s'" % (importSettings.listId, str(type(importSettings.listId))))
        if not importSettings.importSentences and not importSettings.importVocab:
            return
        cardSettings = SmartFMCardTypeSettings()
        modelManager = SmartFMModelManager(importSettings)
        if modelManager.isNeedsVocabModel() or modelManager.isNeedsSentenceModel():
            cardEditDialog = SmartFMModelCustomizeDialog(cardSettings, modelManager.isNeedsVocabModel, modelManager.isNeedsSentenceModel)
            if cardEditDialog.exec_():
                modelManager.createModelsFromSettings(cardSettings)
                QMessageBox.information(mw, "Information", "Created required models, importing...")
                runImport(modelManager, importSettings)
            else:
                QMessageBox.information(mw, "Information", "Cancelled on card types dialog")
        else:
            QMessageBox.information(mw, "Information", "All required models already exist, importing...")
            runImport(modelManager, importSettings)
    else:
        QMessageBox.warning(mw, "Warning", "Cancelled on import settings dialog")


dialogStart = QAction(mw)
dialogStart.setText("iKnow! - Learning Import")
mw.connect(dialogStart, SIGNAL("triggered()"), runDialog)
mw.mainWin.menuTools.addAction(dialogStart)