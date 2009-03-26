iKnow! plugin for Anki
author: Joe Savona (joe savona at gmail dot com)

NOTE: This is not an official product of iKnow! It does, however, use iKnow!'s publicly documented API.

Please see http://wiki.github.com/ridisculous/anki-iknow-importer for the most up to date FAQ. The version at the time of this release is:


Anki smart.fm! Importer

This is the homepage for the (unofficial) smart.fm! import plugin for Anki. With this plugin, you can quickly import items you’ve studied on smart.fm! into your Anki deck. You can also import entire lists into Anki. The plugin allows you to configure Anki’s card templates as you like before importng, so that you can have cards that match the way you want to study.
Features

    * Import vocabulary and sentences, or sentences only
          o Import only the items you’ve actually studied (“My Items”)
          o Or import an entire smart.fm! list
    * Downloads audio samples for each item locally so you can still study offline.
    * Images are referenced so you can see them when you have online acces (per smart.fm!’s terms of use)
    * Customize your card templates before importing to get only the cards you want. You can set up only one card per vocab/sentence, or many. By default there are 3 card templates per item:
          o Reading (question is the expression in Kanji)
          o Listening (question is audio only)
          o Production (question is the meaning of the item, you have to produce the expression)
    * Imports phonetic reading information for languages such as Chinese (pinyin) or Japanese (hiragana/katakana). Currently you cannot select romaji readings for Japanese lists. If you’re studying Japanese, you really, really should learn Hiragana straight away.

Download and Installation

   1. Download the latest version from the downloads page. Choose the highest version number.
   2. Save the .zip file to your Anki plugins directory.
          * On Mac OS X, this is /Users/username/Library/Application Support/Anki/plugins/.
          * To find the plugins directory, open Anki, and choose the menu item Settings->Plugins->Open Plugins Folder
   3. Extract the contents of the zip file. You should have “smart.fm.py” and “smart.fm_importer.py” in the plugins folder now (eg …/Anki/plugins/smart.fm.py)
   4. Restart or open Anki
   5. From the Tools menu, choose the appropriate ‘smart.fm! – ....’ option for what you want to import. See usage below.

Usage

   1. Before importing anything from smart.fm!, choose ‘smart.fm – Customize Models’ from the Tools menu.
   2. You’ll get a message that models have been created, and that you can go edit them now if you like. By default, there are 2 models which have the same card arrangement:
          * Vocab Model:
                o production (given the word in your native language, you have to remember the target language word)
                o reading (given the written word in the target language, remember its meaning)
                o listening (listen to the audio of the word, and try to understand it and remember its
          * Sentence Model (cards are the same as for
                o production
                o reading
                o listening
          * You should not delete either of these models. You should also not rename them. If you do, the plugin will just create them again. However, you can edit the card types. For example, the plugin author himself edits the card types in his deck to look like this:
          * Vocab Model:
                o reading
          * Sentence Model:
                o reading/listening (editing the reading card to also add the audio into the question)
                o production
   3. After you’ve edited the cards to your satisfaction, you’re ready to import some things from smart.fm. Your choices are:
          * User Vocab and Sentences – imports all the items you’ve studied along with smart.fm’s “default” sentences for these items. The sentences may not be ones you’ve studied before. Honestly, it’s a bug in smart.fm’s API. You are asked for the language code of the language you want to study (so that you can limit items/sentences to just one language per smart.fm deck).
          * User Sentences – imports just the sentences for the items you’ve studied. Again, it uses the buggy smart.fm API so you may not have seen all the sentences before.
          * List Vocab and Sentences – this imports only vocab and sentences from the list you enter. This does a full check of the list and ensures sentences are only those that appear in the list (again, working around smart.fm’s buggy API)
          * List Sentences – same as previous but sentences only.
   4. Go ahead and import something! The only thing that’s not supported right now is studying your own language. So english speakers studying english vocab are, unfortunately, out of luck for the moment.

F.A.Q.

Q) I found a bug. What do I do?

A) Email the author (address above) and try to describe it in as much detail. Specifically, what version of Anki, what list were you importing (or if its your user data, just tell me your native language and the language you were trying to study). Also, what operating system are you on?

Q) Where does the reading come from?

A) For Japanese lists, it comes from smart.fm!’s own hiragana/katakana phonetic reading. For all other languages, it comes from the latin/romanized reading. Eg pinyin for chinese. Currently there is no option to get romaji readings for Japanese. Learn Hiragana!

Q) I don’t need audio. Can I skip downloading it?
A) Yes. But because I’m assuming 99% of people will want smart.fm’s awesome audio clips, you have to edit the plugin to disable audio download. Do this: In the Anki plugins directory, change line 14 of ‘iknow_importer.py’ from:

IMPORT_AUDIO = True

to

IMPORT_AUDIO = False

Note the capitalization of ‘False’. The first letter must be capitalized.

Q) How can I highlight (or not highlight) the word for which the sentence is an example?

A) Let’s say that the sentence is “作業するにはもっと広いスペースが必要だ。” and it’s an example for ‘作業’. You have several options for how to display this relationship of sentence/word on the card:
* Make the card’s “meaning” be a combination of the sentence meaning and the meaning for the word. So in the above example, the card meaning would be “I need a bigger space to work. <> 作業—work, operation”. To enable (it’s already enabled by default), edit iknow_importer.py in your plugins directory and make sure line 17 reads:

ENABLE_PRIMARY_WORD_MEANING_IN_SENTENCE_MEANING = True

* Bold the primary word wherever it appears – the front of the card and the back (expression and meaning). To enable (it’s disabled by default), edit iknow_importer.py in your plugins directory and make sure line 20 reads:

ENABLE_PRIMARY_WORD_BOLDING_FOR_BILINGUAL_LISTS = True

* Both of the above

To disable either of these, change ‘True’ to ‘False’

Q) I messed up my username or native language. What do I do?

A) Choose ‘smart.fm – Reset Username and Native Language’ from the Tools menu, and reenter your data.

Q) I ran an import but no items were imported. What’s up with that?

A) i) If there were lots of duplicates, then you probably have just imported that list before. ii) If you know for a fact you haven’t imported that list before, it’s probably one of two things. A) A problem with the script of with smart.fm. If that’s the case you should see some kind of error message. or B) You may have entered an incorrect language code. Either for your native language, or the language you want to study. Try the Tools menu option ‘smart.fm – Reset username and native language’

Q) This plugin is great and makes my life easier. How can I show my appreciation?

A) Email the author and say thanks!
License

This plugin is free. You may edit this plugin and distribute your own derivative, provided that you prominently note the original source of your work and link back to this page.
