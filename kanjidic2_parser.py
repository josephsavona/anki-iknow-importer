from xml.dom import pulldom

class KanjiDicKanji:
    def __init__(self, uKanji):
        self.kanjiChar = uKanji
        self.grade = None
        self.strokeCount = None
        self.frequency = None
        self.jlptLevel = None
        self.radicals = list()
        self.nanori = list()
        self.readingMeaningGroups = list()
        self.dictionaryReferences = {}
        self.queryCodes = {}
    
    def heisigFrameNumber(self):
        if u'heisig' in self.dictionaryReferences:
            return self.dictionaryReferences[u'heisig']
        else:
            return None
    
    def asstr(self):
        str = ""
        str += "-- %s --" % self.kanjiChar.encode('utf-8')
        str += "\n\tgrade:     %s" % self.grade
        str += "\n\tstrokes:   %s" % self.strokeCount
        str += "\n\tfrequency: %s" % self.frequency
        str += "\n\tjlpt level: %s" % self.jlptLevel
        for i, rmgroup in enumerate(self.readingMeaningGroups):
            str += "\n\treading/meaning %s:" % i
            on = ', '.join(map(lambda x: x.encode('utf-8'), rmgroup['on']))
            kun = ', '.join(map(lambda x: x.encode('utf-8'), rmgroup['kun']))
            str += "\n\t\ton: %s" % on
            str += "\n\t\tkun: %s" % kun
            for meaning in rmgroup['meanings']:
                str += "\n\t\t'%s'" % meaning.encode('utf-8')
        nanori = ', '.join(map(lambda x: x.encode('utf-8'), self.nanori))
        str += "\n\tnanori: %s" % nanori
        str += "\n\tdictionary references:"
        for key in self.dictionaryReferences.keys():
            str += "\n\t\t%s: %s" % (key.encode('utf-8'), self.dictionaryReferences[key].encode('utf-8'))
        str += "\n\tquery codes:"
        for key in self.queryCodes.keys():
            str += "\n\t\t%s: %s" % (key.encode('utf-8'), self.queryCodes[key].encode('utf-8'))
        for i, radical in enumerate(self.radicals):
            str += "\n\tradical %s:" % i
            for key in radical.keys():
                str += "\n\t\t%s: %s" % (key.encode('utf-8'), radical[key].encode('utf-8'))
        return str

def q(node, tag):
    return node.getElementsByTagName(tag)

def q1(node, tag):
    nodes = q(node,tag)
    if nodes and len(nodes) > 0:
        return nodes[0]
    else:
        return None

def q1d(node, tag):
    n = q1(node, tag)
    if not n:
        return u""
    text = u""
    for c in n.childNodes:
        text += c.data
    return text

class KanjiDic:
    def __init__(self, path, loadingCallback=None):
        self.kanjiDict = {}
        self.byGrades = {}
        self.byFrequency = {}
        self.byHeisigFrames = {}
        self.loadingCallback = loadingCallback
        
        self._initFromFile(path)
    
    def saveAsSqliteDb(self, path):
        pass
    
    def _initFromFile(self, path):
        kanjiDicFile = open(path)
        events = pulldom.parse(kanjiDicFile)
        for (event, node) in events:
            if event == pulldom.START_ELEMENT:
                if node.tagName.lower() == 'character':
                    events.expandNode(node)
                    self._processNode(node)
    
    def _processNode(self, node):
        kanji = KanjiDicKanji(q1d(node, u'literal'))
        #grade learned in school
        grade = q1d(node, u'grade')
        if len(grade) > 0: 
            kanji.grade = int(grade)
        #stroke count
        kanji.strokeCount = int(q1d(node, u'stroke_count'))
        #frequency of the kanji
        frequency = q1d(node, u'freq')
        if len(frequency) > 0:
            kanji.frequency = int(frequency)
        #jlpt level
        jlptLevel = q1d(node, u'jlpt')
        if len(jlptLevel) > 0:
            kanji.jlptLevel = int(jlptLevel)
        #nanori
        for nanori in q(node, u'nanori'):
            kanji.nanori.append(nanori.firstChild.data)
        #radicals
        for radicalNode in q(node, u'radical'):
            radical = {}
            for rad_value in q(radicalNode, u'rad_value'):
                radical[rad_value.getAttribute(u'rad_type')] = rad_value.firstChild.data
            kanji.radicals.append(radical)
        #dictionary references
        for dicref in q(node, u'dic_ref'):
            kanji.dictionaryReferences[dicref.getAttribute(u'dr_type')] = dicref.firstChild.data
        #query codes
        for qc in q(node, u'q_code'):
            kanji.queryCodes[qc.getAttribute('qc_type')] = qc.firstChild.data
        #reading/meaning groups
        for rmgroup in q(node, u'rmgroup'):
            on = list()
            kun = list()
            meanings = list()
            for reading in q(rmgroup, u'reading'):
                if reading.getAttribute(u'r_type') == u"ja_on":
                    on.append(reading.firstChild.data)
                elif reading.getAttribute(u'r_type') == u"ja_kun":
                    kun.append(reading.firstChild.data)
            for meaning in q(rmgroup, u'meaning'):
                if not meaning.hasAttribute(u'm_lang') or meaning.getAttribute(u'm_lang') == u"en":
                    meanings.append(meaning.firstChild.data)
            kanji.readingMeaningGroups.append({'on' : on, 'kun' : kun, 'meanings' : meanings})
        #save the completed kanji
        #if there's a callback, it should return true/false for a given kanji. if true, we save the kanji. if not, we skip the kanji. allows loading only part of the KanjiDic2 XML file into the dictionary.
        if not self.loadingCallback or (self.loadingCallback and self.loadingCallback(kanji)):
            self.kanjiDict[kanji.kanjiChar] = kanji
            if kanji.grade:
                if not kanji.grade in self.byGrades: self.byGrades[kanji.grade] = list()
                self.byGrades[kanji.grade].append(kanji)
            if kanji.frequency:
                self.byFrequency[kanji.frequency] = kanji
            if u'heisig' in kanji.dictionaryReferences:
                self.byHeisigFrames[int(kanji.dictionaryReferences[u'heisig'])] = kanji
    
    def getKanjiForGrade(self, grade):
        return self.byGrades[grade]
    
    def getKanjiEntry(self, kanjiChar):
        return self.kanjiDict[kanjiChar]
    
    def getKanjiForHeisig(self, heisigFrame):
        return self.byHeisigFrames[heisigFrame]
    
    def getKanjiForFrequency(self, frequency, endRange=None):
        if endRange:
            kanji = list()
            for i in range(frequency, endRange):
                kanji.append(self.byFrequency[i])
            return kanji
        else:
            return self.byFrequency[frequency]
            
if __name__ == "__main__":
    
    def callback(kanji):
        if kanji.grade and kanji.grade == 1:
            print kanji.asstr()
        elif kanji.frequency and kanji.frequency < 25:
            print kanji.asstr()
        else:
            return False
        return True
    
    kanjidict = KanjiDic("kanjidic2.xml", callback)
    