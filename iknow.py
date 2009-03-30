# -*- coding: utf-8 -*-
#added to support SmartFM's XML response type, which is much more accurate and consistent than the API's JSON response type (for example, the XML almost always has a phonetic reading whereas the JSON usually lacks it)
from xml.sax import ContentHandler
from xml.sax import make_parser
from xml.sax.handler import feature_namespaces
#for the smartfm api wrapper
import urllib, urllib2, re, simplejson, os
#for caching of smartfm list data (so that we can save time looking up the list's language and translation language, which are useful when parsing the list itself)
import time, operator, traceback
try:
    from sqlite3 import dbapi2 as sqlite
except:
    from pysqlite2 import dbapi2 as sqlite

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


class SmartFMListScanner(ContentHandler):
    def __init__(self):
        self.lists = {}
        self.current_item = None
        self.current_key = None
        self.collect_chars = None
        
    def startElement(self, name, attrs):
        if name == 'list':
            self.current_item = {'iknow_id' : attrs.get('id'), 'list_uri' : attrs.get('href')}
            self.collect_chars = False
        elif name == 'name':
            self.current_key = 'name'
            self.collect_chars = True
        elif name == 'language' or name == 'translation_language':
            self.current_key = name.lower()
            self.collect_chars= True
        else:
            self.collect_chars = False
            
    def endElement(self, name):
        self.collect_chars = False
        self.current_key = None
        if name == 'list':
            self._addList(self.current_item)
            self.current_item = None
    
    def characters(self, ch):
        if not self.collect_chars:
            return
        elif self.current_item and self.current_key:
            if self.current_key not in self.current_item:
                self.current_item[self.current_key] = u""
            self.current_item[self.current_key] += ch
    
    def _addList(self, newList):
        for key in newList.keys():
            newList[key] = newList[key].strip()
            if len(newList[key]) == 0:
                del list[key]
        if len(newList.keys()) == 0: return
        self.lists[newList['iknow_id']] = newList
    
    def resetItems(self):
        self.lists = {}
    
    def getItems(self):
        return self.lists

#XML SAX handler. Can deal with pretty much any item/sentence/both combination from smartfm. Tested with user:items_studied (with sentences), items:items_in_list, and sentences:sentences_in_list. automatically adjusts the reading/expression (depending on user settings, it seems that what you think might be the expression is actually the reading and vice versa - this class checks for the presence of kanji in the reading and expression and ensure that the right value is in the right place)
class SmartFMItemScanner(ContentHandler):
    def __init__(self, languageCode, translationLanguageCode, includeSentences):
        # Save the name we're looking for
        self.items = {}
        self.current_item = None
        self.current_sentence = None
        self.current_key = None
        self.collect_chars = None
        self.dont_close = None
        self.current_object = None
        self.count = 0
        self.target_language = languageCode.lower()
        self.native_language = translationLanguageCode.lower()
        self.wrong_language = False
        self.includeSentences = includeSentences
        self.preDefinedInformation = {}
        self.itemIndexCounter = 0
    
    def defineBaseInfoForElementIfNotExists(self, iknowId, hash):
        if iknowId not in self.preDefinedInformation:
            self.preDefinedInformation[iknowId] = hash
        #DEBUG
        if hash["_index"] == 61 or iknowId == "sentence:247773":
            print "found minister iknowId %s index %s" % (iknowId, hash["_index"])
        
    def loadPreDefinedInfoIfExists(self, iknowId, hashObject):
        if iknowId in self.preDefinedInformation:
            for key in self.preDefinedInformation[iknowId].keys():
                hashObject[key] = self.preDefinedInformation[iknowId][key]
        
    def startElement(self, name, attrs):
        if name == 'item':
            self.itemIndexCounter += 1
            self.current_item = {'type' : u"item"}
            self.current_item["iknow_id"] = u"item:" + attrs.get('id')
            self.current_item["language"] = attrs.get('language')
            self.loadPreDefinedInfoIfExists(self.current_item["iknow_id"], self.current_item)
            if "_index" not in self.current_item:
                self.current_item["_index"] = self.itemIndexCounter
            self.current_key = None
            self.current_object = self.current_item
            self.current_sentence = None
        elif name == 'sentence':
            self.itemIndexCounter += 1
            if self.current_sentence:
                if attrs.get('language').lower() != self.native_language:
                    self.wrong_language = True
                self.current_key = 'meaning'
                self.dont_close = True
            elif not self.current_sentence:
                self.current_sentence = {'type' : u"sentence"}
                self.current_sentence["iknow_id"] = u"sentence:" + attrs.get('id')
                self.current_sentence["language"] = attrs.get('language')
                self.loadPreDefinedInfoIfExists(self.current_sentence["iknow_id"], self.current_sentence)
                if "_index" not in self.current_sentence:
                    self.current_sentence["_index"] = self.itemIndexCounter
                self.current_key = 'expression'
                self.current_object = self.current_sentence
                if self.current_item:
                    self.current_sentence["item_id"] = self.current_item["iknow_id"]
                elif self.current_sentence["iknow_id"] == "sentence:247773": #DEBUG
                    print "found minister sentence has no item"
        elif name == 'text' or name == 'sound' or name == 'image':
            if self.wrong_language:
                self.collect_chars = False
                return
            self.collect_chars = True
            if name == 'sound':
                self.current_key = 'audio_uri'
            elif name == 'image':
                self.current_key = 'image_uri'
        elif name == 'cue':
            self.current_key = 'expression'
        elif name == 'response' and attrs.get('type') == 'meaning':
            self.current_key = 'meaning'
            if attrs.get('language').lower() != self.native_language:
                self.collect_chars = False
        elif name == 'response' and attrs.get('type') == 'character':
            self.current_key = 'reading'
            if attrs.get('language').lower() != self.target_language:
                self.collect_chars = False
        elif name == 'transliteration':
            self.collect_chars = True
            self.current_key = 'reading@%s' % attrs.get('type').lower()
        
    def characters(self, ch):
        if not self.collect_chars:
            return
        if self.current_object and self.current_key:
            if self.current_key not in self.current_object:
                self.current_object[self.current_key] = ch
            else:
                self.current_object[self.current_key] += ch
    
    def endElement(self, name):
        if name == 'item':
            self._addItem(self.current_object)
            #self.items.append(self.current_object)
            self.current_object = None
            self.current_item = None
        elif name == 'sentence' and self.dont_close:
            self.dont_close = False
            self.wrong_language = False
        elif name == 'sentence':
            self._addItem(self.current_object)
            #self.items.append(self.current_object)
            self.current_sentence = None
            self.current_object = self.current_item
            self.wrong_language = False
        elif name == 'text' or name == 'sound' or name == 'image' or name == 'transliteration':
            self.collect_chars = False
        self.current_key = None
    
    def _addItem(self, item):
        doAddItem = False
        if item["type"] == "sentence" and not self.includeSentences:
            return
        if self.target_language != self.native_language:
            #items translating between languages must have a meaning
            if 'meaning' in item:
                doAddItem = True
        else:
            #items all in one language don't have to have a meaning
            doAddItem = True
        
        if doAddItem:
            rdg = u""
            if 'reading' in item:
                rdg = item['reading']
            elif 'expression' in item:
                item['reading'] = u""
            else:
                return #no reading or expression, so skip this item
            if 'expression' not in item or (self._hasKanji(rdg) and not self._hasKanji(item["expression"])):
                tmp = item['expression']
                item['expression'] = item['reading']
                item['reading@hrkt'] = tmp
            #DEBUG:
            if '_index' in item:
                item['expression'] = item['expression'] + str(item["_index"])
            #DEBUG:
            if item["iknow_id"] == "sentence:247773" or (item["_index"] == 61):
                print "found minister id %s sentence index %s item_id %s" % (item["iknow_id"], item["_index"], "")
                if "item_id" in item:
                    print "\tat item_id %s" % item["item_id"]
            
            for key in item.keys():
                if key == "_index": continue
                item[key] = item[key].strip()
            
            self.items[item['iknow_id']] = item
            self.count += 1

    def _hasKanji(self, chars):
        for char in chars:
            if ord(char) >= int('0x4e00',16) and ord(char) <= int('0x9faf',16):
                return True
        return False
        
    def printItems(self):
        for itemid, item in self.items.iteritems():
            print "\n%s" % (item['iknow_id'])
            for key in sorted(item.keys()):
                if key == 'iknow_id' or key == 'type':
                    continue
                print item[key].encode('utf-8')
    
    def resetItems(self):
        self.items = {}
        
    def getItems(self):
        return self.items

#wrapper class to make it easy to process a bunch of lists from smartfm using the above parser
class SmartFMImporter:
    def __init__(self, handler):
        self.parser = make_parser()
        self.parser.setFeature(feature_namespaces, 0)
        self.handler = handler
        self.parser.setContentHandler(self.handler)
    
    def getItemsFromFile(self, xml):
        self.handler.resetItems()
        self.parser.parse(xml)
        return self.handler.getItems()
    
    def printAll(self):
        self.handler.printItems()


class SmartFMItemSorter:
    def __init__(self):
        pass
        
    def __call__(self, x, y):
        if x["_index"] == y["_index"]:
            if x["type"].lower() == "item" and y["type"].lower() == "sentence":
                return -1
            elif x["type"].lower() == "sentence" and y["type"].lower() == "item":
                return 1
            else:
                return 0
        else:
            return cmp(x["_index"], y["_index"])

class SmartFM:
    SmartFM_STD_URL = "http://smart.fm"
    SmartFM_API_URL = "http://api.smart.fm"
    def __init__(self, username, nativeLangCode):
        self.username = username
        self.nativeLangCode = nativeLangCode
        self.callback = None
    
    def setCallback(self, callback):
        self.callback = callback
    
    def _allItemsUntilEmpty(self, scanner, baseUrl, baseParams, includeSentences, returnAsHash=False, hasManyPages=True):
        perPage = 25
        page = 0
        areMoreItems = True
        importer = SmartFMImporter(scanner)
        allItems = {}
        while areMoreItems:
            page += 1
            currentParams = {}
            currentParams.update(baseParams)
            if hasManyPages:
                currentParams['page'] = page
                currentParams['per_page'] = perPage
            else:
                areMoreItems = False
            if includeSentences:
                currentParams['include_sentences'] = "true"
            currentUrl = baseUrl
            if len(currentParams) > 0 and baseUrl.find("?") < 0:
                currentUrl += "?"
            for i, param in enumerate(currentParams.keys()):
                if i != 0: currentUrl += "&"
                currentUrl += "%s=%s" % (param, currentParams[param])
            if self.callback:
                self.callback(currentUrl, page, len(allItems.keys()))           
            xml = getUrlOrCache(currentUrl)
            items = importer.getItemsFromFile(xml)
            if len(items) > 0 and len(set(items.keys()).difference(set(allItems.keys()))) > 0:
                allItems.update(items)
            else:
                areMoreItems = False
        if returnAsHash:
            return allItems
        else:
            return allItems.values()

    def listItems(self, listId, includeSentences, langCode, translationLanguageCode, returnAsHash=False, includeItems=True):
        scanner = SmartFMItemScanner(langCode, translationLanguageCode, includeSentences)
        allItems = {}
        if includeItems:
            itemsUrl = SmartFM.SmartFM_API_URL + "/lists/%s/items.xml" % listId
            items = self._allItemsUntilEmpty(scanner, itemsUrl, {}, True, True)
            itemValues = items.values()
            itemValues.sort(SmartFMItemSorter())
            for itemorsent in itemValues:
                if itemorsent["type"] == "item":
                    allItems[itemorsent["iknow_id"]] = itemorsent
                elif "item_id" in itemorsent:
                    correspItem = items[itemorsent["item_id"]]
                    scanner.defineBaseInfoForElementIfNotExists(itemorsent["iknow_id"], {"item_meaning" : correspItem['expression'] + " -- " + correspItem["meaning"], "_index" : correspItem["_index"], "core_word" : correspItem['expression']})
        if includeSentences:
            sentencesUrl = SmartFM.SmartFM_API_URL + "/lists/%s/sentences.xml" % listId
            scanner.includeSentences = True
            sentences = self._allItemsUntilEmpty(scanner, sentencesUrl, {}, True, True)
            allItems.update(sentences)
        if returnAsHash:
            return allItems
        else:
            values = allItems.values()
            values.sort(SmartFMItemSorter())
            return values
        
    def userItems(self, includeSentences=True, langCode=None):
        url = SmartFM.SmartFM_API_URL + "/users/%s/items.xml" % self.username
        return self._allItemsUntilEmpty(SmartFMItemScanner(langCode, self.nativeLangCode, includeSentences), url, {}, includeSentences)
    
    def list(self, listId):
        url = SmartFM.SmartFM_API_URL + "/lists/%s.xml" % listId
        lists = self._allItemsUntilEmpty(SmartFMListScanner(), url, {}, False, False, False)
        return lists[0]
    
    def userLists(self):
        url = SmartFM.SmartFM_API_URL + "/users/%s/lists.xml" % self.username
        return self._allItemsUntilEmpty(SmartFMListScanner(), url, {}, False)
    
    def userListItems(self, includeSentences=True, langCode=None):
        allItems = {}
        allLists = self.userLists()
        for iknowlist in allLists:
            if langCode and iknowlist['language'] != langCode:
                continue
            items = self.listItems(iknowlist['iknow_id'], includeSentences, iknowlist['language'], iknowlist['translation_language'], True)
            allItems.update(items)
        return allItems.values()
    
    def matchingItems(self, word, includeSentences, searchLangCode, nativeLangCode=None):
        if not nativeLangCode:
            nativeLangCode = self.nativeLangCode
        url = SmartFM.SmartFM_API_URL + "/items/matching/%s.xml" % (word)
        return self._allItemsUntilEmpty(SmartFMItemScanner(searchLangCode, self.nativeLangCode, includeSentences), url, {"language" : searchLangCode, "translation_language" : nativeLangCode}, includeSentences)
    
    def matchingSentences(self, word, searchLangCode, nativeLangCode=None):
        if not nativeLangCode:
            nativeLangCode = self.nativeLangCode
        url = SmartFM.SmartFM_API_URL + "/sentences/matching/%s.xml" % (word)
        return self._allItemsUntilEmpty(SmartFMItemScanner(searchLangCode, self.nativeLangCode, True), url, {"language" : searchLangCode, "translation_language" : nativeLangCode}, False)
    
    def sentencesForItem(self, listId, itemId, itemExpression, itemLangCode):
        url = SmartFM.SmartFM_STD_URL + "/sentences/matching?keyword=%s&item_id=%s&context=list&course_id=%s&row_id=row_%s&list_builder=lookup_sentences" % (itemExpression.encode('utf-8'), itemId, listId, itemId)
        json = urllib2.urlopen(url)
        sentenceUrls = re.findall(SmartFM.SmartFM_STD_URL + "/sentences/\d+-", json.read())
        allItems = {}
        for url in sentenceUrls:
            match = re.search("sentences/(\d+)-", url)
            if not match:
                continue
            sentenceId = match.group(1)
            items = self._allItemsUntilEmpty(SmartFMItemScanner(itemLangCode, self.nativeLangCode, True), SmartFM.SmartFM_API_URL + "/sentences/%s.xml" % sentenceId, {}, True, True, False)
            allItems.update(items)
        return allItems.values()

class SmartFMCache(SmartFM):
    def __init__(self, username, nativeLangCode, dbPath):
        SmartFM.__init__(self, username, nativeLangCode)
        self.connection = sqlite.connect(dbPath)
        self.connection.row_factory = sqlite.Row
        self.cursor = self.connection.cursor()
        
        self._createDb()
        self.userListsCached = None
        self.userListsCachedTime = None
    
    def _createDb(self):
        try:
            self.cursor.execute("select version from dbversion")
            r = self.cursor.fetchone()
            version = r[0]
        except:
            self.cursor.executescript("""
            create table dbversion(rowid integer primary key, version);
            create table iknow_list(rowid integer primary key, iknow_id integer not null unique, name, list_uri, language, translation_language);
            insert into dbversion (version) values (2);""")
            
    def _storeItemInList(self, itemHash, listId):
        self.cursor.execute("select iknow_id from iknow_items where iknow_id = ?", (int(itemHash['iknow_id']),))
        r = self.cursor.fetchone()
        if r and len(r) > 0:
            pass
        else:
            self.cursor.execute("insert into iknow_items(iknow_id, json_data) values (?,?)", (itemHash['iknow_id'], simplejson.dumps(itemHash)))
        
        self.cursor.execute("select * from iknow_list_item where iknow_list_id = ? and iknow_item_id = ?", (listId, itemHash['iknow_id']))
        r = self.cursor.fetchone()
        if r and len(r) > 0:
            pass
        else:
            self.cursor.execute("insert into iknow_list_item(iknow_list_id, iknow_item_id) values(?,?)", (listId, itemHash['iknow_id']))
        self.connection.commit()
    
    def _storeList(self, listHash):
        self.cursor.execute("select iknow_id from iknow_list where iknow_id = ?", (int(listHash["iknow_id"]),))
        r = self.cursor.fetchone()
        if r and len(r) > 0:
            return
        self.cursor.execute("insert into iknow_list(iknow_id, name, list_uri, language, translation_language) values (?, ?, ?, ?, ?)", (int(listHash["iknow_id"]), listHash["name"], listHash["list_uri"], listHash["language"], listHash["translation_language"]))
        self.connection.commit()
        
    def _storeLists(self, listHash=None, listHashList=None):
        if listHash:
            self._storeList(listHash)
        if listHashList:
            for listhash in listHashList:
                self._storeList(listhash)
    
    def _getList(self, listId):
        self.cursor.execute("select * from iknow_list where iknow_id = ?", (listId,))
        r = self.cursor.fetchone()
        if r and len(r) > 0:
            return r    
    
    def list(self, listId):
        try:
            iknowlist = self._getList(listId)
            if iknowlist:
                return iknowlist
            iknowlist = SmartFM.list(self, listId)
            self._storeList(listHash = iknowlist)
            return iknowlist
        except:
            raise SmartFMDownloadError(traceback.format_exc())
    
    def listItems(self, listId, includeSentences=True, returnAsHash=False):
        try:
            iknowlist = self.list(listId)
            return SmartFM.listItems(self, listId, includeSentences, iknowlist["language"], iknowlist['translation_language'], returnAsHash)
        except:
            raise SmartFMDownloadError(traceback.format_exc())
    
    def userLists(self):
        try:
            timeNow = time.time()
            if self.userListsCached and timeNow - self.userListsCachedTime < 300: #cache five minutes, I imagine most people will probably run a couple imports in a row, possibly, and then not import for a while
                return self.userListsCached
            userLists = SmartFM.userLists(self)
            self._storeLists(listHashList = userLists)
            self.userListsCached = userLists
            self.userListsCachedTime = time.time()
            return userLists
        except:
            raise SmartFMDownloadError(traceback.format_exc())
    
    def userListItems(self, includeSentences=True, langCode=None):
        try:
            userLists = self.userLists()
            allItems = {}
            for iknowlist in userLists:
                listItems = self.listItems(iknowlist["iknow_id"], includeSentences, True)
                allItems.update(listItems)
            return allItems.values()
        except:
            raise SmartFMDownloadError(traceback.format_exc())
        

if __name__ == "__main__":
    print "This is a module for importing into other scripts. To see some examples, uncomment some of the code in the EXAMPLES section."
    
    #convenience function to print out a vocab word or sentence
    def printItem(item):
        transliterations = list()
        for key in item.keys():
            try:
                item[key] = item[key].encode('utf-8')
            except:
                pass
            if key.find("reading") >= 0:
                transliterations.append(key)
        print "id:\t%s" % item["iknow_id"]
        print "meaning:\t%s\nexpression:\t%s\ntype:\t%s" % (item["meaning"], item["expression"], item["type"])
        if "_index" in item:
            print "index:\t%s" % (item["_index"])
        if "core_word" in item:
            print "core word:\t%s" % (item['core_word'])
        if "item_meaning" in item:
            print "item meaning:\t%s" % (item["item_meaning"])
        for key in transliterations:
            print "%s:\t%s" % (key.encode('utf-8'), item[key])
        print ""
    
    #EXAMPLES: lines with one # are code, those with ## are comments
    
    ## Create an SmartFM API wrapper object with a default username and the user's native language code. Third parameter is either ':memory:' for an in memory cache, or "/Path/To/File.db" if you want to save the cache somewhere for reuse. List information is cached, to eliminate the need for repeated lookups of list information. List information is used so that you don't need to specify the language and translation language of a list manually when you grab list items/sentences.
    
    #START HERE - uncomment this
    #iknow = SmartFMCache("username", "en", ":memory:") #use a file path for the 3rd parameter if you want to save the cache somewhere.
    
    #EXAMPLE 1
    ## List Items English Core 2000 Step 1, for Japanese learners. Uses a new SmartFMCache object because we're using a different native language here. Includes sentences
    def callback(currentUrl, page, items):
        print "getting %s page %s with %s items so far" % (currentUrl, page, items)
    iknowJp = SmartFMCache("username", "en", ":memory:")
    iknowJp.setCallback(callback)
    core2k1 = iknowJp.listItems(19056, True) 
        #chinese media for english speakers: 35430
        #japanese core 2k 19056
        #english to english SAT 700
    for item in core2k1:
        printItem(item)
    
    #OTHER EXAMPLES ARE BELOW
    ## Sentences for a given item (vocab word), as it appears in a given list of a given langauge. Not part of the offical iKnow! API, this is using the JSON response that iKnow's own listbuilder uses when you select sentences for an item in your list.
    #params:
    #   your list ID (make your own public list for adding items to)
    #   the item ID
    #   the expression of the item
    #   the language of the item
    #sentences = iknow.sentencesForItem(1234, 438118, u"具合", "ja")
    
    ## List Items Japanese Core 2000 Step 1 for english learners, including sentences
    #core2k1 = iknow.listItems(19053, True)
        
    ## List Items English Core 2000 Step 1, for Japanese learners. Uses a new SmartFMCache object because we're using a different native language here. Includes sentences
    #def callback(currentUrl, page, items):
    #    print "getting %s page %s with %s items so far" % (currentUrl, page, items)
    #iknowJp = SmartFMCache("username", "en", ":memory:")
    #iknowJp.setCallback(callback)
    #core2k1 = iknowJp.listItems(19056, True) #chinese media for english speakers: 35430
    #for item in core2k1:
    #    printItem(item)
    
    ## All the japanese items in all the user's lists
    #user_list_items = iknow.userListItems(False, "ja")
    
    ## User's lists
    #user_lists = iknow.userLists()
    
    ## All the user's japanese items, including sentences
    #user_items = iknow.userItems(True, "ja")
    
    ## Items matching 'business', with no sentences
    #bus_items = iknow.matchingItems("business", False, "en", "ja")
    
    ## English sentences matching 'business', with translation language set to japanese
    #bus_sent = iknow.matchingSentences("business","en", "ja")
