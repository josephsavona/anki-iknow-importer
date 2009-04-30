# -*- coding: utf-8 -*-
import unittest
from iknow import SmartFMAPI

class ListDataLoadsProperly(unittest.TestCase):
    
    def testEnglishToJapaneseList(self):
        api = SmartFMAPI("debug.txt")
        smartfmlist = api.list(19056)
        self.failUnlessEqual(u"Japanese Core 2000:Step 3", smartfmlist.name)
        self.failUnlessEqual(u"en", smartfmlist.translation_language)
        self.failUnlessEqual(u"ja", smartfmlist.language)
        self.failUnlessEqual(u"http://smart.fm/lists/19056", smartfmlist.list_uri)
        self.failUnlessEqual(u"19056", smartfmlist.iknow_id)
        self.failUnlessEqual("list:19056", smartfmlist.uniqIdStr())
        api._close()
    
    def testEnglishToEnglishList(self):
        api = SmartFMAPI("debug.txt")
        smartfmlist = api.list(700)
        self.assertEqual(u"SAT Beginner".lower(), smartfmlist.name.lower(), "List name does not match website")
        self.assertEqual(u"en", smartfmlist.translation_language, "Translation language should be 'en'")
        self.assertEqual(u"en", smartfmlist.language, "List language should be 'en'")
        self.assertEqual(u"http://smart.fm/lists/700", smartfmlist.list_uri)
        self.assertEqual(u"700", smartfmlist.iknow_id)
        self.assertEqual("list:700", smartfmlist.uniqIdStr())
        api._close()


class ListVocabOnly(unittest.TestCase):
    def testSATBeginnerVocab(self):
        api = SmartFMAPI("debug.txt")
        vocab = api.listItems(700, True, False)
        self.assertEqual(250, len(vocab), "There should be 250 vocab words")
        for word in vocab:
            self.assertEqual(u"item", word.type, "Vocab 'type' should be 'item'")
            self.failIfEqual(None, word.meaning)
        self.failUnlessEqual(u"context", vocab[0].expression.strip())
        self.failUnlessEqual(u"conventional", vocab[1].expression.strip())
        self.failUnlessEqual(u"comprehensive", vocab[2].expression.strip())
        self.failUnlessEqual(u"commodity", vocab[25].expression.strip())
        self.failUnlessEqual(u"critique", vocab[50].expression.strip())
        api._close()
    
    def testChineseMediaVocab(self):
        api = SmartFMAPI("debug.txt")
        vocab = api.listItems(35430, True, False)
        self.failUnlessEqual(317, len(vocab))
        self.failUnlessEqual(u"465646", vocab[0].iknow_id)
        self.failUnlessEqual(u"465648", vocab[1].iknow_id)
        self.failUnlessEqual(u"466049", vocab[-1].iknow_id)
        api._close()
    
    def testJapaneseToEnglishVocab(self):
        api = SmartFMAPI("debug.txt")
        vocab = api.listItems(19056, True, False)
        self.assertEqual(200, len(vocab), "there should be 200 vocab words")
        for word in vocab:
            self.failUnlessEqual(u"item", word.type)
            self.failIfEqual(None, word.meaning)
        self.failUnlessEqual(u"問題", vocab[0].expression, "First word not correct")
        self.failUnlessEqual(u"開発", vocab[1].expression, "Second word not correct")
        self.failUnlessEqual(u"事件", vocab[2].expression, "Third word not correct")
        self.failUnlessEqual(u"頃", vocab[26].expression, "27th word not correct")
        self.failUnlessEqual(u"ほとんど", vocab[50].expression, "50th word not correct. should mean 'influence, effect' but it means %s" % vocab[50].meaning[0])
        api._close()
    
    def testPoroporoTearsFullData(self):
        api = SmartFMAPI("debug.txt")
        testVocab = api.item(790286)
        self.failUnlessEqual(u"ぽろぽろ", testVocab.expression, "expression wrong on test vocab word")
        self.failUnlessEqual(u"poroporo", testVocab.reading.replace('<b>','').replace('</b>','').lower(), "reading should be romaji")
        self.failUnlessEqual(None, testVocab.audio_uri, "should have no audio")
        self.failUnlessEqual(None, testVocab.image_uri, "should have no image")
        self.failUnlessEqual(u"(shed tears) in large drops", testVocab.meaning.replace('<b>','').replace('</b>',''))
        self.failUnlessEqual(u"http://smart.fm/item/790286", testVocab.item_uri)
        self.failUnlessEqual(u"ja", testVocab.language)
        api._close()
    
    def testSentenceSnow(self):
        api = SmartFMAPI("debug.txt")
        sentence = api.sentence(243210, u"en")
        self.failUnlessEqual(u"家の外に積もった雪でドアがふさがれてしまった。", sentence.expression.replace('<b>','').replace('</b>',''), "expression invalid")
        self.failUnlessEqual(u"いえ の そと に つもった ゆき で ドア が ふさがれてしまった 。", sentence.reading.replace('<b>','').replace('</b>',''), "reading invalid")
        self.failUnlessEqual(u"The snow outside our house blocked the door.", sentence.meaning.replace('<b>','').replace('</b>',''))
        self.failUnlessEqual(u"", sentence.audio_uri)
        self.failUnlessEqual(u"http://assets0.smart.fm/assets/legacy/images/01/2932927.jpg", sentence.image_uri)
        self.failUnlessEqual(u"http://smart.fm/sentences/243210", sentence.item_uri)
        self.failUnlessEqual(u"ja", sentence.language)
        api._close()
    
    def testItemMondaiProblem(self):
        api = SmartFMAPI("debug.txt")
        item = api.item(436164)
        self.failUnlessEqual(u"http://assets1.smart.fm/assets/legacy/JLL/audio/JW09359A.mp3", item.audio_uri)
        api._close()
        

class SentencesOnly(unittest.TestCase):
    def testSATBeginnerSentenceNoMeaningButKeywordMeaning(self):
        api = SmartFMAPI("debug.txt")
        sentences = api.listItems(700, False, True)
        for sentence in sentences:
            self.assertEqual(u"sentence", sentence.type)
            self.assertEqual(None, sentence.meaning, "Single language list sentences have no 'meaning' or translation.")
            self.assert_(len(sentence.secondary_meanings) > 0, "List sentences should all have at least one secondary meaning: %s" % sentence.expression)
        api._close()
    
    def testSATBeginnerSentenceOrder(self):
        #check that sentences are in the correct order    
        api = SmartFMAPI("debug.txt")
        sentences = api.listItems(700, False, True)
        for sentence in sentences:
            self.failIfEqual(None, sentence.expression)
        self.failUnlessEqual(u"Seeing something in a different <b>context</b> than the accustomed one can be surprising.", sentences[0].expression.strip())
        self.failUnlessEqual(u"He works in a very <b>conventional</b> work environment.", sentences[1].expression.strip())
        self.failUnlessEqual(u"She gained <b>comprehensive</b> knowledge of baseball after dating him for a year.", sentences[2].expression.strip())
        self.failUnlessEqual(u"They enjoyed working in <b>conjunction</b> with one another.", sentences[24].expression.strip())
        self.failUnlessEqual(u"My college prides itself on its ethnically <b>diverse</b> student population.", sentences[30].expression.strip())
        api._close()
    
    def testJapaneseToEnglishSentenceOrder(self):
        api = SmartFMAPI("debug.txt")
        sentences = api.listItems(19056, False, True)
        for sentence in sentences:
            self.failIfEqual(None, sentence.meaning)
            self.failIfEqual(None, sentence.expression)
        self.failUnlessEqual(u"問題が一つあります。", sentences[0].expression.replace(u"<b>",u'').replace(u"</b>",u''))
        self.assert_(sentences[0].reading.replace(u"<b>",u"").replace(u"</b>",u"").find(u"もんだい が ひとつ あります") >= 0, "Reading not correct for first sentence")
        
        self.failUnlessEqual(u"247757", sentences[0].iknow_id)
        self.failUnlessEqual(u"247759", sentences[1].iknow_id)
        self.failUnlessEqual(u"247761", sentences[2].iknow_id)
        self.failUnlessEqual(u"247815", sentences[29].iknow_id)
        api._close()
        
    def testListLengths(self):
        self.checkListLength(19056, 200)
        self.checkListLength(35430, 660)
        self.checkListLength(700, 250)
    
    def checkListLength(self, listId, count):
        api = SmartFMAPI("debug.txt")
        sentences = api.listItems(listId, False, True)
        self.failUnlessEqual(count, len(sentences))
        api._close() 
    
    def testBilingualListSentencesHaveMeaning(self):
        self.checkListItemsSentencesAlwaysHaveAMeaning(19056)
        self.checkListItemsSentencesAlwaysHaveAMeaning(35430)
    
    def checkListItemsSentencesAlwaysHaveAMeaning(self, listId):
        api = SmartFMAPI("debug.txt")
        sentences = api.listItems(listId, False, True)
        for sentence in sentences:
            self.assert_(len(sentence.meaning) > 0, "All sentence should have at least one meaning.")
        api._close()
    
    def testListSentencesOnlyReturnSentences(self):
        self.checkListItemsSentencesReturnsOnlySentences(19056)
        self.checkListItemsSentencesReturnsOnlySentences(700)
        self.checkListItemsSentencesReturnsOnlySentences(35430)
    
    def checkListItemsSentencesReturnsOnlySentences(self, listId):
        api = SmartFMAPI("debug.txt")
        sentences = api.listItems(listId, False, True)
        for sentence in sentences:
            self.assertEqual(u"sentence", sentence.type)
        api._close()
    
class VocabAndSentences(unittest.TestCase):
    def testChineseMediaHasSimpleAndTraditionalCharacters(self):
        api = SmartFMAPI("debug.txt")
        items = api.listItems(35430, True, False)
        for item in items:
            self.failIfEqual(None, item.meaning)
            self.failIfEqual(None, item.expression)
        self.assert_(items[3].expression.find(u"市場") >= 0, "Should have simple/traditional characters")
        self.assert_(items[3].expression.find(u"市场") >= 0, "Should also have Hansig characters")
        items = api.listItems(35430, False, True)
        self.assert_(items[0].expression.find(u"龍是中") >= 0, "Should have simple/traditional characters")
        self.assert_(items[0].expression.find(u"龙是中") >= 0, "Should also have Hansig characters")
        api._close()
    
    def testJapaneseToEnglishAll(self):
        api = SmartFMAPI("debug.txt")
        items = api.listItems(19056, True, True)
        wordCount = 0
        sentenceCount = 0
        index = 0
        for item in items:
            if item.type == "item":
                wordCount += 1
            elif item.type == "sentence":
                sentenceCount += 1
        self.failUnlessEqual(200, wordCount)
        self.failUnlessEqual(200, sentenceCount)
        
        self.failUnlessEqual(u"436164", items[0].iknow_id)
        self.failUnlessEqual(u"247757", items[1].iknow_id)
        api._close()
        
    def testJapaneseToEnglishWordsBeforeTheirSentences(self):
        self.checkListForVocabThenSentencesOrder(19056)
    
    def testSATBeginnerWordsBeforeTheirSentences(self):
        self.checkListForVocabThenSentencesOrder(700)
    
    def testChineseMediaWordsBeforeSentences(self):
        self.checkListForVocabThenSentencesOrder(35430)
    
    def checkListForVocabThenSentencesOrder(self, listId):
        api = SmartFMAPI("debug.txt")
        items = api.listItems(listId, True, True)
        vocab = api.listItems(listId, True, False)
        curWordIndex = 0
        curWord = None
        #loop through the items and ensure that:
        #   a) vocabulary appears in the same order as on the list itself on smart.fm
        #   b) sentences appear only immediately after the last keyword in the sentence. if the sentence contains two keywords from the current list, then it should appear immediately after the second vocabulary word. this ensures the user has already seen the necessary vocabulary to understand a sentence
        # eg:
        #   vocab 1
        #   sentence for vocab 1
        #   vocab 2
        #   sentence for vocab 2
        #   sentence 2 for vocab 2
        for i, item in enumerate(items):
            if not curWord:
                self.assertEqual(u"item", item.type)
                self.assertEqual(vocab[0].iknow_id, item.iknow_id)
                curWord = item
            elif item.type == "item":
                curWordIndex += 1
                self.assertEqual(vocab[curWordIndex].iknow_id, item.iknow_id)
                curWord = item
            elif item.type == "sentence":
                self.assertEqual(curWord.expression, item.core_words[-1], "Every sentence should be an example for the word that preceded it. current word is\n %s\nsentence is\n%s\nitem number %s" % (curWord.meaning, item.meaning, i))
        api._close()
    
if __name__ == "__main__":
    unittest.main()