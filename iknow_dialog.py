from PyQt4.QtCore import SIGNAL
from PyQt4.QtGui import QAction, QMessageBox
from PyQt4 import QtCore, QtGui
from ankiqt import mw
from ankiqt.ui.utils import getOnlyText
from anki.models import Model, FieldModel, CardModel
from anki.facts import Field
import os, re, time, urllib
from iknow import IknowCache


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

class IknowImportDialog(QtGui.QDialog):
    def __init__(self):
        QtGui.QDialog.__init__(self)
        self.setObjectName("iKnow Import")
        self.setWindowTitle(_("iKnow! Import"))
        self.resize(450, 600)
    
        self.mainLayout = QtGui.QVBoxLayout(self)
        self.mainLayout.setObjectName("mainLayout")
    
        # what to import
        #   items, sentences, OR both
        #   list URL OR user items
        #   max items to import (new items) (by default this is equally spread between items and sentences if both are selected)
        self.settingsBox = QtGui.QGroupBox("Import Settings", self)
        self.settingsLayout = QtGui.QVBoxLayout(self.settingsBox)
        self.mainLayout.addWidget(self.settingsBox)
        
        self.labelSource = QtGui.QLabel("Items to download. Enter an iKnow! list URL or your iKnow! username:")
        self.settingsLayout.addWidget(self.labelSource)
        self.txt_source = QtGui.QTextEdit(self)
        self.txt_source.setMinimumSize(100,20)
        self.settingsLayout.addWidget(self.txt_source)
    
        self.rbtn_group_typesToImport = QtGui.QGroupBox("Item types to import:", self)
        self.rbtnLayout = QtGui.QVBoxLayout(self.rbtn_group_typesToImport)
        self.rbtn_typesToImportVocab = QtGui.QRadioButton("&Vocabulary", self.rbtn_group_typesToImport)
        self.rbtnLayout.addWidget(self.rbtn_typesToImportVocab)
        self.rbtn_typesToImportSent = QtGui.QRadioButton("&Sentences", self.rbtn_group_typesToImport)
        self.rbtnLayout.addWidget(self.rbtn_typesToImportSent)
        self.rbtn_typesToImportAll = QtGui.QRadioButton("&All", self.rbtn_group_typesToImport)
        self.rbtnLayout.addWidget(self.rbtn_typesToImportAll)
        self.settingsLayout.addWidget(self.rbtn_group_typesToImport)
    
        self.labelAmount = QtGui.QLabel("Amount of items to import (1 or more):")
        self.settingsLayout.addWidget(self.labelAmount)
        self.txt_amountToImport = QtGui.QTextEdit(self)
        self.txt_amountToImport.setMinimumSize(50,20)
        self.settingsLayout.addWidget(self.txt_amountToImport)
        
        self.btnStartImport = QtGui.QPushButton(self)
        self.btnStartImport.setText(_("Start Import"))
        self.btnStartImport.setDefault(True)
        self.settingsLayout.addWidget(self.btnStartImport)
        
        self.importStatusLabel = QtGui.QLabel("")
        self.settingsLayout.addWidget(self.importStatusLabel)
    
        # embedded reviewer with question is Expression + Reading, answer is Meaning
        self.reviewerWidget = EmbeddedReviewer(mw, self, self.mainLayout)
    
        # learn area
        #   expression
        #   reading
        #   meaning
        #   next button (adds the actual item/sentence to the deck, and retrieves the next NEW item/sentence for showing in the learn area
        self.cancelButton = QtGui.QPushButton(self)
        self.cancelButton.setText(_("Finish"))
        self.mainLayout.addWidget(self.cancelButton)
        
        self.connect(self.btnStartImport, QtCore.SIGNAL("clicked()"), self.startImportClicked)
        self.connect(self.cancelButton, QtCore.SIGNAL("clicked()"), self.cancelClicked)
        
        self.exec_()
        
    def startImportClicked(self):
        self.btnStartImport.setEnabled(False)
        pass
    
    def cancelClicked(self):
        self.close()

def runDialog():
    #try:
        dialog = IknowImportDialog()
        dialog.show()
    #except:
    #   QMessageBox.warning(mw, "Warning","The RTK Import plugin could not run properly. Please check that you have installed all the necessary files. See the readme file (Settings->Plugins->Show Plugins Directory: file 'RTK_IMPORT_README') for details.")

dialogStart = QAction(mw)
dialogStart.setText("iKnow! - Learning Import")
mw.connect(dialogStart, SIGNAL("triggered()"),
    runDialog)
mw.mainWin.menuTools.addAction(dialogStart)