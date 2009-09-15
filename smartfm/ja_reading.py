# -*- coding: utf-8 -*-
foundJapaneseSupportPlugin = False
mecabInstance = None
try:
    from japanese.reading import MecabController
    foundJapaneseSupportPlugin = True
    mecabInstance = MecabController()
except:
    pass

FIRST_HIRAGANA = ord(u"ぁ")
LAST_HIRAGANA = ord(u"ゖ")
FIRST_KATAKANA = ord(u"ァ")
LAST_CONVERTIBLE_KATAKANA = ord(u"ヶ")
KANA_OFFSET = FIRST_KATAKANA - FIRST_HIRAGANA

def asHiraganaOrEmpty(char):
    charOrd = ord(char)
    if charOrd >= FIRST_HIRAGANA and charOrd <= LAST_HIRAGANA:
        return char
    elif charOrd >= FIRST_KATAKANA and charOrd <= LAST_CONVERTIBLE_KATAKANA:
        return unichr(charOrd - KANA_OFFSET)
    else:
        return u""

def kanaOnly(string):
    kanaStr = u""
    for c in unicode(string):
        kanaStr += asHiraganaOrEmpty(c)
    return kanaStr
    
if not foundJapaneseSupportPlugin:
    def getAdjustedReadingOfText(originalText, originalReading):
        """given the original text, use JA support mecab plugin to find the reading. if the mecab reading matches the original reading, return the mecab formatted version (ie with kanjitext[kanareading] form). if the mecab reading does not match the original reading, return None."""
        return (originalReading, "original")
else:
    def getAdjustedReadingOfText(originalText, originalReading):
        """given the original text, use JA support mecab plugin to find the reading. if the mecab reading matches the original reading, return the mecab formatted version (ie with kanjitext[kanareading] form). if the mecab reading does not match the original reading, return None."""
        try:
            mecabReading = mecabInstance.reading(originalText)
            if len(originalReading) == 0:
                return (mecabReading, "differentreading")
            elif kanaOnly(originalReading) != kanaOnly(mecabReading):
                return (None, "differentreading")
            else:
                return (mecabReading, "mecab")
        except:
            return (originalReading, "original")