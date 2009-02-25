from kanjidic2_parser import KanjiDic
import os

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from ankiqt import mw
from ankiqt.ui.utils import getOnlyText
from anki.models import Model, FieldModel, CardModel
from anki.facts import Field

KANJI_MODEL = u"RTK - Kanji"

def ensureKanjiModelExists():
    model = None
    for m in mw.deck.models:
        if m.name.lower() == KANJI_MODEL.lower():
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
    
def getFrameNumber():
    gotInt = False
    while not gotInt:
        frame = getOnlyText("Enter the highest frame number you have studied, or 'q' to quit:")
        if len(frame.strip()) > 0:
            try:
                if frame.lower() == 'q':
                    return 0
                return int(frame)
            except:
                pass

def isKanjiHasHeisigFrame(kanji):
    if kanji.heisigFrameNumber():
        return True
    else:
        return False

def addHeisigFrame():
    kanjiModel = ensureKanjiModelExists()
    maxFrameNumber = getFrameNumber()
    if maxFrameNumber == 0: return
    kanjiDic = None
    
    for frame in range(1, maxFrameNumber+1):
        if not kanjiDic:
            kanjiDictPath = os.path.join(mw.pluginsFolder(), 'JPdictionaryFiles', 'kanjidic2.xml')
            kanjiDic = KanjiDic(kanjiDictPath, isKanjiHasHeisigFrame)
        
        heisigFrame = u"heisig:%s" % (frame)
        query = mw.deck.s.query(Field).filter_by(value=heisigFrame)
        field = query.first()
        if field:
            continue
        kanji = kanjiDic.getKanjiForHeisig(frame)
        keyword = getOnlyText("Enter a keyword for the kanji: %s  (%s)" % (kanji.kanjiChar, frame))
        story = getOnlyText("Enter a story for the kanji: %s  (%s)" % (kanji.kanjiChar, frame))
        primitives = getOnlyText("Enter any primitive meanings for the kanji: %s  (%s)" % (kanji.kanjiChar, frame))
        
        strokeDiagramPath = os.path.join(mw.pluginsFolder(), u'JPdictionaryFiles', u'sod-utf8', kanji.kanjiChar + u'.png')
        strokeAnimationPath = os.path.join(mw.pluginsFolder(), u'JPdictionaryFiles', u'soda-utf8', kanji.kanjiChar + u'.gif')
        
        fact = mw.deck.newFact(kanjiModel)
        fact[u'Kanji'] = kanji.kanjiChar
        fact[u'FrameNumber'] = heisigFrame
        fact[u'Keyword'] = keyword
        fact[u'Story'] = story
        fact[u'PrimitiveMeanings'] = primitives
        ankiDiagramPath = mw.deck.addMedia(strokeDiagramPath)
        ankiAnimationPath = mw.deck.addMedia(strokeAnimationPath)
        fact[u'Image_StrokeOrderDiagram'] = u'<img src="%s"/>' % (ankiDiagramPath)
        fact[u'Image_StrokeOrderAnimation'] = u'<img src="%s" />' % (ankiAnimationPath)
        mw.deck.addFact(fact)
        mw.deck.save()
        mw.reset()

addKanji = QAction(mw)
addKanji.setText("RTK - Add Kanji")
mw.connect(addKanji, SIGNAL("triggered()"),
    addHeisigFrame)

mw.mainWin.menuTools.addSeparator()
mw.mainWin.menuTools.addAction(addKanji)

