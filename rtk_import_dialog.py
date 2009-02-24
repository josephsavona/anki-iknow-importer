from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtCore, QtGui
from ankiqt.ui.main import AnkiQt
from ankiqt import mw
from ankiqt.ui.utils import getOnlyText
from anki.models import Model, FieldModel, CardModel
from anki.facts import Field
import os
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
        
        self.currentKanjiFrame = None
        self.determineNextKanji()
        
        self.setObjectName("RTK Kanji Import")
        self.setWindowTitle(_("RTK Kanji Import"))
        self.resize(450, 600)
        
        #main layout
        self.vboxlayout = QtGui.QVBoxLayout(self)
        self.vboxlayout.setObjectName("vboxlayout")
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
        #self.fld_story.setFormat(PyQt.PlainText)
        self.settingsLayout.addWidget(self.fld_story)
        #   primitive meanings
        self.settingsLayout.addWidget(QtGui.QLabel(_("Primitive Meanings:")))
        self.fld_primitives = QtGui.QTextEdit(self)
        self.fld_primitives.setObjectName("primitives")
        self.fld_primitives.setMinimumSize(100,100)
        #self.fld_primitives.setFormat(PyQt.PlainText)
        self.settingsLayout.addWidget(self.fld_primitives)
        
        self.addButton = QtGui.QPushButton(self)
        self.addButton.setText(_("Add Kanji"))
        self.addButton.setDefault(True)
        self.vboxlayout.addWidget(self.addButton)
        
        self.cancelButton = QtGui.QPushButton(self)
        self.cancelButton.setText(_("Finish"))
        self.vboxlayout.addWidget(self.cancelButton)
        
        self.connect(self.addButton, QtCore.SIGNAL("clicked()"), self.addClicked)
        self.connect(self.cancelButton, QtCore.SIGNAL("clicked()"), self.cancelClicked)
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
            model = Model(KANJI_MODEL)
            model.addFieldModel(FieldModel(u'Kanji', True, True))
            model.addFieldModel(FieldModel(u'FrameNumber', True, True))
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
        model = self.ensureKanjiModelExists()
        strokeDiagramPath = os.path.join(mw.pluginsFolder(), u'JPdictionaryFiles', u'sod-utf8', self.currentKanji + u'.png')
        strokeAnimationPath = os.path.join(mw.pluginsFolder(), u'JPdictionaryFiles', u'soda-utf8', self.currentKanji + u'.gif')
        
        fact = mw.deck.newFact(model)
        #TODO pull data from UI field
        fact[u'Kanji'] = self.currentKanji
        fact[u'FrameNumber'] = u"heisig:%s" % self.currentKanjiFrame
        fact[u'Keyword'] = unicode(self.fld_keyword.text())
        fact[u'Story'] = unicode(self.fld_story.toPlainText())
        fact[u'PrimitiveMeanings'] = unicode(self.fld_primitives.toPlainText())
        ankiDiagramPath = mw.deck.addMedia(strokeDiagramPath)
        fact[u'Image_StrokeOrderDiagram'] = u'<img src="%s"/>' % (ankiDiagramPath)
        ankiAnimationPath = mw.deck.addMedia(strokeAnimationPath)
        fact[u'Image_StrokeOrderAnimation'] = u'<img src="%s" />' % (ankiAnimationPath)
        mw.deck.addFact(fact)
        mw.deck.save()
        mw.reset()
        self.statusLabel.setText("Added card for kanji: %s" % self.currentKanji)
        self.incrementKanji()
    
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
    dialog = RTKImportDialog()
    dialog.show()

dialogStart = QAction(mw)
dialogStart.setText("RTK Import")
mw.connect(dialogStart, SIGNAL("triggered()"),
    runDialog)
mw.mainWin.menuTools.addAction(dialogStart)