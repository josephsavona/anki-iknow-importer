iKnow! plugin for Anki
author: Joe Savona (joe savona at gmail dot com)

NOTE: This is not an official product of iKnow! It does, however, use iKnow!'s publicly documented API.

========== USAGE ===========

1) Before importing anything from iKnow!, choose 'iKnow - Customize Models' from the Tools menu.
2) You'll get a message that models have been created, and that you can go edit them now if you like. By default, there are 2 models which have the same card arrangment:

    Vocab Model:
    * production (given the word in your native language, you have to remember the target language word)
    * reading (given the written word in the target language, remember its meaning)
    * listening (listen to the audio of the word, and try to understand it and remember its meaning)
    
    Sentence Model (cards are the same as for vocab):
    * production
    * reading
    * listening
    
You should *not* delete either of these models. You should also *not* rename them. If you do, the plugin will just create them again. However, you can edit the card types. For example, the plugin author himself edits the card types in his deck to look like this:

    Vocab Model:
    * reading
    
    Sentence Model:
    * reading/listening (editing the reading card to also add the audio into the question)
    * production
    
3) After you've edited the cards to your satisfaction, you're ready to import some things from iKnow. Your choices are:
    * User Vocab and Sentences - imports all the items you've studied along with iKnow's "default" sentences for these items. The sentences may not be ones you've studied before. Honestly, it's a bug in iKnow's API. You are asked for the language code of the language you want to study (so that you can limit items/sentences to just one language per iknow deck).
    * User Sentences - imports just the sentences for the items you've studied. Again, it uses the buggy iKnow API so you may not have seen all the sentences before.
    
    * List Vocab and Sentences - this imports only vocab and sentences from the list you enter. This does a full check of the list and ensures sentences are only those that appear in the list (again, working around iKnow's buggy API)
    * List Sentences - same as previous but sentences only.

4) Go ahead and import something! The only thing that's not supported right now is studying your own language. So english speakers studying english vocab are, unfortunately, out of luck for the moment. 

=========== FAQ ==============

Q) I found a bug. What do I do?
A) Email the author (address above) and try to describe it in as much detail. Specifically, what version of Anki, what list were you importing (or if its your user data, just tell me your native language and the language you were trying to study). Also, what operating system are you on?

Q) Where does the reading come from?
A) For Japanese lists, it comes from iKnow!'s own hiragana/katakana phonetic reading. For all other languages, it comes from the latin/romanized reading. Eg pinyin for chinese.

Q) I don't need audio. Can I skip downloading it? 
A) No. Sorry, one of the great things about iKnow is the high quality audio recordings available, and I'm assuming almost everyone will want to use those for their studies.

Q) I messed up my username or native language. What do I do?
A) Choose 'iKnow - Reset Username and Native Language' from the Tools menu, and reenter your data.

Q) I ran an import but no items were imported. What's up with that?
A) i) If there were lots of duplicates, then you probably have just imported that list before. 
   ii) If you know for a fact you haven't imported that list before, it's probably one of two things. A) A problem with the script of with iKnow. If that's the case you should see some kind of error message. or B) You may have entered an incorrect language code. Either for your native language, or the language you want to study. Try the Tools menu option 'iKnow - Reset username and native language' 
   
Q) This plugin is great and makes my life easier. How can I show my appreciation?
A) Email the author and say thanks!
