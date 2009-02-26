from PyQt4.QtCore import SIGNAL
from PyQt4.QtGui import QAction, QMessageBox
from PyQt4 import QtCore, QtGui
from ankiqt import mw
from ankiqt.ui.utils import getOnlyText
from anki.models import Model, FieldModel, CardModel
from anki.facts import Field
import os, time
try:
    from sqlite3 import dbapi2 as sqlite
except:
    from pysqlite2 import dbapi2 as sqlite

class EmbeddedReviewer:
    
    BASE_INTERVAL = 2.2
    FAIL_INTERVAL = 1
    def __init__(self, mainWindow, parentDialog, container):
        self.reviewItems = {}
        self.currentReviewItem = None
        
        box = QtGui.QGroupBox("Quick Review", parentDialog)
        layout = QtGui.QVBoxLayout(box)
        container.addWidget(box)
        
        self.lblReviewQuestion = QtGui.QLabel("")
        layout.addWidget(self.lblReviewQuestion)
        
        self.btnFlipCardButton = QtGui.QPushButton(parentDialog)
        self.btnFlipCardButton.setText(_("Flip Card"))
        layout.addWidget(self.btnFlipCardButton)
        parentDialog.connect(self.btnFlipCardButton, QtCore.SIGNAL("clicked()"), self.callbackFlipCardClicked)
        
        self.btnYesButton = QtGui.QPushButton(parentDialog)
        self.btnYesButton.setText(_("Remembered"))
        layout.addWidget(self.btnYesButton)
        parentDialog.connect(self.btnYesButton, QtCore.SIGNAL("clicked()"), self.callbackYesButtonClicked)
        
        self.btnNoButton = QtGui.QPushButton(parentDialog)
        self.btnNoButton.setText(_("Forgot"))
        layout.addWidget(self.btnNoButton)
        parentDialog.connect(self.btnNoButton, QtCore.SIGNAL("clicked()"), self.callbackNoButtonClicked)
        self.refresh()
    
    def callbackFlipCardClicked(self):
        if self.currentReviewItem:
            (answer, showTime, interval) = self.reviewItems[self.currentReviewItem]
            self.lblReviewQuestion.setText(answer)
            self.setState(2)
        else:
            self.refresh() #don't refresh if there is a current item for review
    
    def callbackYesButtonClicked(self):
        if self.currentReviewItem:
            (answer, showTime, interval) = self.reviewItems[self.currentReviewItem]
            diff = (time.time() - showTime)
            interval = interval * EmbeddedReviewer.BASE_INTERVAL
            self.reviewItems[self.currentReviewItem] = (answer, time.time() + diff + 60 * interval , interval)
        self.refresh()
    
    def callbackNoButtonClicked(self):
        if self.currentReviewItem:
            (answer, showTime, interval) = self.reviewItems[self.currentReviewItem]
            self.reviewItems[self.currentReviewItem] = (answer, time.time() + EmbeddedReviewer.FAIL_INTERVAL * 60, EmbeddedReviewer.FAIL_INTERVAL)
        self.refresh()
    
    def setState(self, state):
        if state == 0:
            self.btnNoButton.setEnabled(False)
            self.btnYesButton.setEnabled(False)
            self.btnFlipCardButton.setEnabled(False)
        elif state == 1:
            self.btnFlipCardButton.setEnabled(True)
            self.btnYesButton.setEnabled(False)
            self.btnNoButton.setEnabled(False)
        elif state == 2:
            self.btnFlipCardButton.setEnabled(False)
            self.btnYesButton.setEnabled(True)
            self.btnNoButton.setEnabled(True)
    
    def refresh(self):
        nextKey, earliestTime = None, time.time()
        for key in self.reviewItems.keys():
            (answer, showTime, interval) = self.reviewItems[key]
            if showTime < earliestTime:
                nextKey = key
                earliestTime = showTime
        if nextKey:
            self.lblReviewQuestion.setText(nextKey)
            self.currentReviewItem = nextKey
            self.setState(1)
        else:
            self.lblReviewQuestion.setText("")
            self.currentReviewItem = None
            self.setState(0)
    
    def addQuestionAnswerForReview(self, question, answer):
        self.reviewItems[question] = (answer, time.time() + EmbeddedReviewer.BASE_INTERVAL * 60, EmbeddedReviewer.BASE_INTERVAL)
        self.refresh()

class RTKImportDialog(QtGui.QDialog):
    MAX_HEISIG = 3007
    KANJI_MODEL = u"RTK - Kanji"
    
    def __init__(self):
        QtGui.QDialog.__init__(self)
        heisigSqlFile = os.path.join(mw.pluginsFolder(), "JPdictionaryFiles", "RTKkanji.sqlite")
        self.conn = sqlite.connect(heisigSqlFile)
        self.conn.row_factory = sqlite.Row
        self.cursor = self.conn.cursor()
        
        self.currentKanjiFrame = None
        self.determineNextKanji()
        
        self.setObjectName("RTK Kanji Import")
        self.setWindowTitle(_("RTK Kanji Import"))
        self.resize(450, 600)
        
        #main layout
        self.vboxlayout = QtGui.QVBoxLayout(self)
        self.vboxlayout.setObjectName("vboxlayout")
        
        #embedded reviewer for added kanji
        self.reviewerWidget = EmbeddedReviewer(mw, self, self.vboxlayout)
        
        #settings sublayout
        self.settingsBox = QtGui.QGroupBox("Card Details", self)
        self.settingsLayout = QtGui.QVBoxLayout(self.settingsBox)
        self.vboxlayout.addWidget(self.settingsBox)

        #   kanji label
        self.kanjiLabel = QtGui.QLabel("<b>" + _("Kanji") + "</b>" + (": %s" % self.currentKanji))
        self.settingsLayout.addWidget(self.kanjiLabel)
        #   keyword
        self.settingsLayout.addWidget(QtGui.QLabel(_("Keyword:")))
        self.fld_keyword = QtGui.QLineEdit(self)
        self.fld_keyword.setObjectName("keyword")
        self.fld_keyword.setMinimumSize(100,20)
        self.settingsLayout.addWidget(self.fld_keyword)
        #   story
        self.settingsLayout.addWidget(QtGui.QLabel(_("Story:")))
        self.fld_story = QtGui.QTextEdit(self)
        self.fld_story.setObjectName("story")
        self.fld_story.setMinimumSize(100,100)
        self.settingsLayout.addWidget(self.fld_story)
        #   primitive meanings
        self.settingsLayout.addWidget(QtGui.QLabel(_("Primitive Meanings:")))
        self.fld_primitives = QtGui.QTextEdit(self)
        self.fld_primitives.setObjectName("primitives")
        self.fld_primitives.setMinimumSize(100,100)
        self.settingsLayout.addWidget(self.fld_primitives)
        
        #   status label
        self.statusLabel = QtGui.QLabel("")
        self.vboxlayout.addWidget(self.statusLabel)
        
        self.addButton = QtGui.QPushButton(self)
        self.addButton.setText(_("Add Kanji"))
        self.addButton.setDefault(True)
        self.vboxlayout.addWidget(self.addButton)
        
        self.cancelButton = QtGui.QPushButton(self)
        self.cancelButton.setText(_("Finish"))
        self.vboxlayout.addWidget(self.cancelButton)
        
        self.connect(self.addButton, QtCore.SIGNAL("clicked()"), self.addClicked)
        self.connect(self.cancelButton, QtCore.SIGNAL("clicked()"), self.cancelClicked)
        self.fld_keyword.setFocus()
        self.exec_()
        
    def determineNextKanji(self):
        if self.currentKanjiFrame:
            self.currentKanjiFrame += 1
        else:
            for i in range(1, RTKImportDialog.MAX_HEISIG + 1):
                query = mw.deck.s.query(Field).filter_by(value=u"heisig:%s" % i)
                field = query.first()
                if not field:
                    self.currentKanjiFrame = i
                    break
        self.cursor.execute("select kanji from rtk_kanji where heisig_frame = ?", (self.currentKanjiFrame,))
        row = self.cursor.fetchone()
        if not row:
            #TODO: show message "no more Heisig Kanji"
            self.cancelClicked()
        else:
            self.currentKanji = row["kanji"]

    def ensureKanjiModelExists(self):
        model = None
        for m in mw.deck.models:
            if m.name.lower() == RTKImportDialog.KANJI_MODEL.lower():
                return m
        if not model:
            model = Model(RTKImportDialog.KANJI_MODEL)
            model.addFieldModel(FieldModel(u'Kanji', True, True))
            model.addFieldModel(FieldModel(u'HeisigFrameID', True, True))
            model.addFieldModel(FieldModel(u'Keyword', True, True))
            model.addFieldModel(FieldModel(u'Story', True, True))
            model.addFieldModel(FieldModel(u'PrimitiveMeanings', False, False))
            model.addFieldModel(FieldModel(u'Image_StrokeOrderDiagram', False, False))
            model.addFieldModel(FieldModel(u'Image_StrokeOrderAnimation', False, False))
            model.addCardModel(CardModel(
                u'Remembering',
                u'%(Keyword)s',
                u'%(Kanji)s<br>%(Story)s<br>%(PrimitiveMeanings)s<br>%(Image_StrokeOrderAnimation)s<br>%(Image_StrokeOrderDiagram)s'))
            mw.deck.addModel(model)
        return model
       
    def addClicked(self):
        try:
            model = self.ensureKanjiModelExists()
            
            fact = mw.deck.newFact(model)
            #TODO pull data from UI field
            fact[u'Kanji'] = self.currentKanji
            fact[u'HeisigFrameID'] = u"heisig:%s" % self.currentKanjiFrame
            fact[u'Keyword'] = unicode(self.fld_keyword.text())
            fact[u'Story'] = unicode(self.fld_story.toPlainText())
            fact[u'PrimitiveMeanings'] = unicode(self.fld_primitives.toPlainText())
            
            strokeDiagramPath = os.path.join(mw.pluginsFolder(), u'JPdictionaryFiles', u'sod-utf8', self.currentKanji + u'.png')
            if os.path.exists(strokeDiagramPath):
                ankiDiagramPath = mw.deck.addMedia(strokeDiagramPath)
                fact[u'Image_StrokeOrderDiagram'] = u'<img src="%s"/>' % (ankiDiagramPath)
            else:
                fact[u'Image_StrokeOrderDiagram'] = u""
            
            strokeAnimationPath = os.path.join(mw.pluginsFolder(), u'JPdictionaryFiles', u'soda-utf8', self.currentKanji + u'.gif')
            if os.path.exists(strokeAnimationPath):
                ankiAnimationPath = mw.deck.addMedia(strokeAnimationPath)
                fact[u'Image_StrokeOrderAnimation'] = u'<img src="%s" />' % (ankiAnimationPath)
            else:
                fact[u'Image_StrokeOrderAnimation'] = u""
            
            mw.deck.addFact(fact)
            mw.deck.save()
            mw.reset()
            self.statusLabel.setText("Added card for kanji: %s" % self.currentKanji)
            self.reviewerWidget.addQuestionAnswerForReview(unicode(self.fld_keyword.text()), self.currentKanji)
            self.incrementKanji()
        except:
            QMessageBox.warning(mw, "Warning","Your card may contain duplicate data. Please check that you have the correct keyword and that you haven't re-used the keyword or story before by accident. If you are sure there is no duplicate, then please contact the developer.")
    
    def incrementKanji(self):
        self.determineNextKanji()
        self.kanjiLabel.setText("<b>" + _("Kanji") + "</b>" + (": %s" % self.currentKanji))
        self.fld_story.setText(u"")
        self.fld_primitives.setText(u"")
        self.fld_keyword.setText(u"")
        self.fld_keyword.setFocus()
    
    def cancelClicked(self):
        self.conn.close()
        self.close()

def runDialog():
    try:
        dialog = RTKImportDialog()
        dialog.show()
    except:
        QMessageBox.warning(mw, "Warning","The RTK Import plugin could not run properly. Please check that you have installed all the necessary files. See the readme file (Settings->Plugins->Show Plugins Directory: file 'RTK_IMPORT_README') for details.")

dialogStart = QAction(mw)
dialogStart.setText("RTK - Add Kanji")
mw.connect(dialogStart, SIGNAL("triggered()"),
    runDialog)
mw.mainWin.menuTools.addAction(dialogStart)