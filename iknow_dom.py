from xml.dom import pulldom, Node
import os, urllib, urllib2, re, operator

#CACHE_API_RESULTS_PATH = None #remove comment from beginning of this line, and add comment to next line, in order to cache results
#TODO
CACHE_API_RESULTS_PATH = os.path.join("/tmp", "smartfm_api_cache") #Set to 'None' (no quotes) to disable caching. do *not* enable unless you are debugging this script

#API CACHING - useful for script debugging or if you know your lists won't be changing (if there is ANY chance your list might change, disable this)
if CACHE_API_RESULTS_PATH:
    if not os.path.exists(CACHE_API_RESULTS_PATH):
        try:
            os.mkdir(CACHE_API_RESULTS_PATH)
        except:
            CACHE_API_RESULTS_PATH = None
if CACHE_API_RESULTS_PATH:    
    import sha
    def getUrlOrCache(url):
        if url[-1] == "?":
            url = url[0:-1]
        hasher = sha.new(url)
        hashedFilename = os.path.join(CACHE_API_RESULTS_PATH, hasher.hexdigest())
        #DEBUG: print "caching %s at %s" % (url, hashedFilename)
        if not os.path.exists(hashedFilename):
            urllib.urlretrieve(url, hashedFilename)
        return open(hashedFilename)
else:
    def getUrlOrCache(url):
        if url[-1] == "?":
            url = url[0:-1]
        return urllib2.urlopen(url)


class SmartFMDownloadError(Exception):
    pass

class SmartFMListItemsMustFetchSomethingError(Exception):
    pass

class SmartFMNoListDataFound(Exception):
    pass

def q(node, tag):
    return node.getElementsByTagName(tag)

def qallwa(node, tag, attribute, value):
    nodes = q(node, tag)
    matchingNodes = list()
    if nodes.length > 0:
        for node in nodes:
            if node.hasAttribute(attribute) and node.getAttribute(attribute).lower() == value.lower():
                matchingNodes.append(node)
    return matchingNodes


def q1(node, tag):
    nodes = q(node,tag)
    if nodes and len(nodes) > 0:
        return nodes[0]
    else:
        return None

def qwa(node, tag, attribute, value):
    nodes = q(node, tag)
    for n in nodes:
        if n and n.hasAttribute(attribute):
            attrValue = n.getAttribute(attribute)
            if attrValue and attrValue == value:
                return n
    return None

def qnodetext(node):
    text = u""
    for c in node.childNodes:
        text += c.data
    return text

def q1d(node, tag):
    n = q1(node, tag)
    if not n:
        return u""
    text = u""
    for c in n.childNodes:
        text += c.data
    return text
    
class SmartFMList(object):
    def __init__(self):
        self.iknow_id = None
        self.list_uri = None
        self.name = None
        self.language = None
        self.translation_language = None
        self.type = u"list"
        self.index = None
    
    def uniqIdStr(self):
        return self.type + u":" + self.iknow_id
    
    def loadFromDOM(self, node):
        self.iknow_id = node.getAttribute(u'id')
        self.language = q1d(node, u'language')
        self.translation_language = q1d(node, u'translation_language')
        self.list_uri = node.getAttribute(u'href')
        self.name = q1d(node, u'name')
    
    def __repr__(self):
        return "id: %s\n\tlist uri: %s\n\tname: %s\n\tlang: %s\n\ttrans lang: %s\n\t" % (self.iknow_id, self.list_uri, self.name, self.language, self.translation_language)
    

class SmartFMItem(object):
    def __init__(self):
        self.iknow_id = None
        self.language = None
        self.index = None
        self.meaning = None
        self.secondary_meanings = list()
        self.expression = None
        self.reading = None
        self.audio_uri = None
        self.image_uri = None
        self.item_uri = None
        
    def uniqIdStr(self):
        return self.type + u":" + self.iknow_id
    
    def __repr__(self):
        return "id: %s\n\tlang: %s\n\tmeaning: %s\n\texpr: %s\n\tread: %s\n\taudio: %s\n\t img: %s\n\ttype: %s\n" % (self.iknow_id, self.language, self.meaning, self.expression, self.reading, self.audio_uri, self.image_uri, self.type)

class SmartFMVocab(SmartFMItem):
    def __init__(self):
        SmartFMItem.__init__(self)
        self.type = u"item"
    
    def loadFromDOM(self, node):
        self.iknow_id = node.getAttribute(u'id')
        self.language = node.getAttribute(u'language')
        self.item_uri = node.getAttribute(u'href')
        charNode = None
        if q1(node, u'character'):
            self.expression = q1d(node, u'character')
            if q1(node, u'text'):
                self.reading = q1d(node, u'text')
        elif q1(node, u'text'):
            self.expression = q1d(node, u'text')
        if not self.reading:
            readingNode = qwa(node, u'transliteration', u'type', u'Latn')
            if readingNode:
                self.reading = qnodetext(readingNode)
        meaningNode = qwa(node, u'response', u'type', u'meaning')
        if meaningNode:
            self.meaning = q1d(meaningNode, u'text')
        if q1(node, u'sound'):
            self.audio_uri = q1d(node, u'sound')
        if q1(node, u'image'):
            self.image_uri = q1d(node, u'image')
        
    def sentencesFromDOM(self, node, translationLanguage):
        sentencesNode = q1(node, u'sentences')
        sentenceslist = list()
        for sentenceNode in sentencesNode.childNodes:
            if sentenceNode.nodeType == Node.ELEMENT_NODE and sentenceNode.tagName.lower() == "sentence":
                nextsentence = SmartFMSentence()
                nextsentence.loadFromDOM(sentenceNode, translationLanguage)
                nextsentence.linkToVocab(self)
                sentenceslist.append(nextsentence)
        return sentenceslist
        
class SmartFMSentence(SmartFMItem):
    def __init__(self):
        SmartFMItem.__init__(self)
        self.type = u"sentence"
    
    def linkToVocab(self, vocab):
        newMeaning = u"<br />" + vocab.expression + u" -- " + vocab.meaning
        self.secondary_meanings.append(newMeaning)
    
    def loadFromDOM(self, node, translationLanguage):
        self.iknow_id = node.getAttribute(u'id')
        self.language = node.getAttribute(u'language')
        self.item_uri = node.getAttribute(u'href')
        self.expression = q1d(node, u'text')
        readingNode = qwa(node, u'transliteration', u'type', u'Hrkt')
        if readingNode:
            self.reading = qnodetext(readingNode)
        else:
            readingNode = qwa(node, u'transliteration', u'type', u'Latn')
            if readingNode:
                self.reading = qnodetext(readingNode)
        meaningSentenceNode = qwa(node, u'sentence', u'language', translationLanguage)
        if meaningSentenceNode:
            self.meaning = q1d(meaningSentenceNode, u'text')
        if q1(node, u'sound'):
            self.audio_uri = q1d(node, u'sound')
        if q1(node, u'image'):
            self.image_uri = q1d(node, u'image')

class SmartFMAPIResultSet(object):
    def __init__(self, startIndex=0):
        self.lists = {}
        self.items = {}
        self.current_index = startIndex
    
    def addList(self, newlist):
        if newlist.uniqIdStr() in self.lists:
            return False
        self.current_index += 1
        newlist.index = self.current_index
        self.lists[newlist.uniqIdStr()] = newlist
        return True
        
    def addItem(self, newitem):
        if newitem.uniqIdStr() in self.items:
            return False
        self.current_index += 1
        newitem.index = self.current_index
        self.items[newitem.uniqIdStr()] = newitem
        return True
    
    def sortItems(self, yesVocab, yesSentences):
        for key in self.items.keys():
            if self.items[key].type == "vocab" and not yesVocab:
                del self.items[key]
            elif self.items[key].type == "sentence" and not yesSentences:
                del self.items[key]
        values = self.items.values()
        values.sort(key=operator.attrgetter('index'))
        return values
    
    def mergeWithResults(self, resultSet):
        hasAtLeastOneUpdate = False
        if len(resultSet.lists) > 0:
            if len(set(resultSet.lists.keys()).difference(set(self.lists.keys()))) > 0:
                self.lists.update(resultSet.lists)
                hasAtLeastOneUpdate = True
        if len(resultSet.items) > 0:
            if len(set(resultSet.items.keys()).difference(set(self.items.keys()))) > 0:
                self.items.update(resultSet.items)
                hasAtLeastOneUpdate = True
        if hasAtLeastOneUpdate:
            return True
        else:
            return False

class SmartFMAPI(object):
    SmartFM_STD_URL = "http://smart.fm"
    SmartFM_API_URL = "http://api.smart.fm"
    
    def __init__(self, logFile=None):
        self.debug = True
        if self.debug and logFile:
            self.log = open(logFile, 'a')
            self.log.write("\n\n----------------------START----------------------\n")
        else:
            self.log = None
    
    def _logMsg(self, msg):
        if self.debug and self.log:
            self.log.write(str(msg) + "\n")
            self.log.flush()
    
    def _close(self):
        if self.debug and self.log:
            self.log.flush()
            self.log.close()
        
    def _parsePage(self, xml, pageResults, translationLanguage, includeSentences):
        events = pulldom.parse(xml)
        changedItemCount = 0
        for (event, node) in events:
            if event == pulldom.START_ELEMENT:
                if node.tagName.lower() == 'list':
                    events.expandNode(node)
                    smartfmlist = SmartFMList()
                    smartfmlist.loadFromDOM(node)
                    #self._logMsg(smartfmlist)
                    if pageResults.addList(smartfmlist):
                        changedItemCount += 1
                elif node.tagName.lower() == 'item':
                    events.expandNode(node)
                    smartfmitem = SmartFMVocab()
                    smartfmitem.loadFromDOM(node)
                    #self._logMsg(smartfmitem)
                    if pageResults.addItem(smartfmitem):
                        changedItemCount += 1
                    if includeSentences:
                        for sentence in smartfmitem.sentencesFromDOM(node, translationLanguage):
                            #self._logMsg(sentence)
                            if pageResults.addItem(sentence):
                                changedItemCount += 1
                            elif sentence.uniqIdStr() in pageResults.items:
                                pageResults.items[sentence.uniqIdStr()].linkToVocab(smartfmitem)
                elif includeSentences and node.tagName.lower() == 'sentence':
                    events.expandNode(node)
                    smartfmsentence = SmartFMSentence()
                    smartfmsentence.loadFromDOM(node, translationLanguage)
                    pageResults.addItem(smartfmsentence)
                    changedItemCount += 1
        return changedItemCount
    
    def _allPagesUntilEmpty(self, baseUrl, baseParams={}, translationLanguage=None, moreThanOnePage=True, includeSentences=False, startResultSet=None):
        page = 0
        perPage = 25
        areMoreItems = True
        currentUrl = None
        currentParams = None
        newItemsOnPageCount = None
        totalResults = SmartFMAPIResultSet()
        if startResultSet:
            totalResults = startResultSet
        while areMoreItems:
            page += 1
            self._logMsg("page fetch loop, page %s with %s lists and %s items" % (page, len(totalResults.lists), len(totalResults.items)))
            currentParams = {}
            currentParams.update(baseParams)
            currentParams["per_page"] = perPage
            currentParams["page"] = page
            currentUrl = baseUrl + u"?"
            for i, key in enumerate(currentParams.keys()):
                if i != 0: currentUrl += u"&"
                currentUrl += "%s=%s" % (key, currentParams[key])
            self._logMsg("fetching url %s" % currentUrl)
            xml = getUrlOrCache(currentUrl)
            newItemsOnPageCount = self._parsePage(xml, totalResults, translationLanguage, includeSentences)
            if newItemsOnPageCount > 0:
                self._logMsg("at least one new list/item retrieved")
            else:
                self._logMsg("no new lists/items retrieved, breaking loop")
                areMoreItems = False
            if not moreThanOnePage:
                areMoreItems = False
        self._logMsg("all pages fetched, got %s lists and %s items" % (len(totalResults.lists), len(totalResults.items)))
        return totalResults
    
    def list(self, listId):
        self._logMsg("list(%s)" % listId)
        url = SmartFMAPI.SmartFM_API_URL + "/lists/%s.xml" % listId
        results = self._allPagesUntilEmpty(url, moreThanOnePage=True)
        if len(results.lists.values()) > 0:
            return results.lists.values()[0]
        else:
            raise SmartFMNoListDataFound, "No data could be retrieved for smart.fm list %s" % listId
            
        
    
    def listItems(self, listId, includeVocab, includeSentences):
        smartfmlist = self.list(listId)
        if includeVocab and includeSentences:
            return self.listItemsAll(smartfmlist)
        elif includeVocab:
            return self.listVocab(smartfmlist)
        elif includeSentences:
            return self.listSentences(smartfmlist)
        else:
            raise SmartFMListItemsMustFetchSomethingError, "listItems() called but no item type (vocab, sentence, both) specified"
        
    def listVocab(self, smartfmlist):
        self._logMsg("listVocab(%s)" % smartfmlist.iknow_id)
        itemsUrlBase = SmartFMAPI.SmartFM_API_URL + "/lists/%s/items.xml" % smartfmlist.iknow_id
        itemsParamsBase = {"include_sentences" : "false"}
        results = self._allPagesUntilEmpty(itemsUrlBase, baseParams=itemsParamsBase, includeSentences=False)
        return results.sortItems(True, False)
    
    def listSentences(self, smartfmlist):
        self._logMsg("listSentences(%s)" % smartfmlist.iknow_id)
        baseUrl = SmartFMAPI.SmartFM_API_URL + "/lists/%s/sentences.xml" % smartfmlist.iknow_id
        results = self._allPagesUntilEmpty(baseUrl, translationLanguage=smartfmlist.translation_language, moreThanOnePage=False, includeSentences=True)
        return results.sortItems(False, True)
            
    
    def listItemsAll(self, smartfmlist):
        self._logMsg("listItemsAll(%s)" % smartfmlist.iknow_id)
        itemsUrlBase = SmartFMAPI.SmartFM_API_URL + "/lists/%s/items.xml" % smartfmlist.iknow_id
        itemsBaseParams = {"include_sentences" : "true"} #we want the data for the sentences so that we can tie vocab words to the sentences
        allResults = self._allPagesUntilEmpty(itemsUrlBase, baseParams=itemsBaseParams, includeSentences=True, translationLanguage=smartfmlist.translation_language)
        sentUrl = SmartFMAPI.SmartFM_API_URL + "/lists/%s/sentences.xml" % smartfmlist.iknow_id
        sentenceResults = self._allPagesUntilEmpty(sentUrl, translationLanguage=smartfmlist.translation_language, moreThanOnePage=False, includeSentences=True)
        for key in allResults.items.keys():
            if allResults.items[key].type == "sentence":
                if key not in sentenceResults.items:
                    del allResults.items[key]
        return allResults.sortItems(True, True)