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

class RTKImportDialog(QtGui.QDialog):
    MAX_HEISIG = 3007
    KANJI_MODEL = u"RTK - Kanji"
    
    def __init__(self):
        QtGui.QDialog.__init__(self)
        heisigSqlFile = os.path.join(mw.pluginsFolder(), "JPdictionaryFiles", "RTKkanji.sqlite")
        self.conn = sqlite.connect(heisigSqlFile)
        self.conn.row_factory = sqlite.Row
        self.cursor = self.conn.cursor()
        
        self.review_kanji = {}
        self.current_review_kanji = None
        
        self.currentKanjiFrame = None
        self.determineNextKanji()
        
        self.setObjectName("RTK Kanji Import")
        self.setWindowTitle(_("RTK Kanji Import"))
        self.resize(450, 600)
        
        #main layout
        self.vboxlayout = QtGui.QVBoxLayout(self)
        self.vboxlayout.setObjectName("vboxlayout")
        #review sublayout
        self.reviewBox = QtGui.QGroupBox("Quick Review", self)
        self.reviewLayout = QtGui.QHBoxLayout(self.reviewBox)
        self.vboxlayout.addWidget(self.reviewBox)
        #   review keyword
        self.rvwKeyword = QtGui.QLabel("")
        self.reviewLayout.addWidget(self.rvwKeyword)
        #   review show button
        self.rvwShowButton = QtGui.QPushButton(self)
        self.rvwShowButton.setText(_("Show"))
        self.reviewLayout.addWidget(self.rvwShowButton)
        self.rvwYesButton = QtGui.QPushButton(self)
        self.rvwYesButton.setText(_("Remembered"))
        self.reviewLayout.addWidget(self.rvwYesButton)
        self.rvwNoButton = QtGui.QPushButton(self)
        self.rvwNoButton.setText(_("Forgot"))
        self.reviewLayout.addWidget(self.rvwNoButton)
        
        #settings sublayout
        self.settingsBox = QtGui.QGroupBox("Card Details", self)
        self.settingsLayout = QtGui.QVBoxLayout(self.settingsBox)
        self.vboxlayout.addWidget(self.settingsBox)
        #   status label
        self.statusLabel = QtGui.QLabel("")
        self.settingsLayout.addWidget(self.statusLabel)
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
        
        #   review area
        self.reviewLabel = QtGui.QLabel("")
        self.settingsLayout.addWidget(self.reviewLabel)
        
        self.addButton = QtGui.QPushButton(self)
        self.addButton.setText(_("Add Kanji"))
        self.addButton.setDefault(True)
        self.vboxlayout.addWidget(self.addButton)
        
        self.cancelButton = QtGui.QPushButton(self)
        self.cancelButton.setText(_("Finish"))
        self.vboxlayout.addWidget(self.cancelButton)
        
        self.connect(self.addButton, QtCore.SIGNAL("clicked()"), self.addClicked)
        self.connect(self.cancelButton, QtCore.SIGNAL("clicked()"), self.cancelClicked)
        self.connect(self.rvwShowButton, QtCore.SIGNAL("clicked()"), self.reviewShowClicked)
        self.connect(self.rvwYesButton, QtCore.SIGNAL("clicked()"), self.reviewYesClicked)
        self.connect(self.rvwNoButton, QtCore.SIGNAL("clicked()"), self.reviewNoClicked)
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
            self.review_kanji[self.currentKanji] = [time.time() + 60, unicode(self.fld_keyword.text()), 60]
            self.updateReview()
            self.incrementKanji()
        #except FactInvalidError:
        #    QMessageBox.warning(mw, "Warning", "One or more fields was not unique. Please check your keyword and story and ensure that they are unique for this Kanji.")
        except:
            QMessageBox.warning(mw, "Warning","Your card may contain duplicate data. Please check that you have the correct keyword and that you haven't re-used the keyword or story before by accident. If you are sure there is no duplicate, then please contact the developer.")
    
    def updateReview(self):
        nextKanji, earliestTime = None, time.time()
        for kanji in self.review_kanji.keys():
            reviewTime = self.review_kanji[kanji][0]
            if reviewTime < earliestTime:
                nextKanji = kanji
                earliestTime = reviewTime
        if nextKanji:
            self.current_review_kanji = nextKanji
            self.rvwKeyword.setText(self.review_kanji[nextKanji][1])
        else:
            self.current_review_kanji = None
            self.rvwKeyword.setText("")
    
    def reviewShowClicked(self):
        if self.current_review_kanji:
            keyword = self.review_kanji[self.current_review_kanji][1]
            self.rvwKeyword.setText("%s: %s" % (keyword, self.current_review_kanji))
        else:
            QMessageBox.information(mw, "Information", "No current kanji. There are %s kanji in review" % (len(self.review_kanji)))
    
    def reviewYesClicked(self):
        if self.current_review_kanji:
            kanji = self.current_review_kanji
            self.review_kanji[kanji][0] = time.time() + self.review_kanji[kanji][2] * 2
            self.review_kanji[kanji][2] = self.review_kanji[kanji][2] * 2
            self.updateReview()
        else:
            QMessageBox.information(mw, "Information", "No current kanji. There are %s kanji in review" % (len(self.review_kanji)))
    
    def reviewNoClicked(self):
        if self.current_review_kanji:
            kanji = self.current_review_kanji
            self.review_kanji[kanji][0] = time.time() + 60
            self.review_kanji[kanji][2] = 60
            self.updateReview()
        else:
            QMessageBox.information(mw, "Information", "No current kanji. There are %s kanji in review" % (len(self.review_kanji)))
    
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