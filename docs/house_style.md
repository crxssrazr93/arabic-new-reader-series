# House Style

These conventions follow how Arabic grammar and Islamic texts are traditionally taught. A reviewing teacher may change any of them.

## Honorifics

* **The Prophet Muhammad**: ﷺ after every mention, by name or title (the Prophet, the Messenger of Allah), in the English lines, glosses' English lines, notes and boxes. In the Arabic sentences, write it out after النَّبِيُّ / رَسُولُ اللَّهِ / مُحَمَّدٌ as four words with empty glosses: `[صَلَّى, ""], [اللَّهُ, ""], [عَلَيْهِ, ""], [وَسَلَّمَ, ""]` (the student reads the words; booklet 3's tip teaches that scholars dislike shortening it). ﷺ is used in English text only. Never the abbreviation (ص) or "(pbuh)".
* **Other prophets and Maryam**: at the first mention in each story, Arabic `عَلَيْهِ السَّلَامُ` (عَلَيْهَا for Maryam, عَلَيْهِمُ for a plural) as words in the sentence, glossed `[عَلَيْهِ, upon him]`, `[السَّلَامُ, (be) peace]`; English line "(peace be upon him)". In dictionary notes and boxes, at the first mention in each entry or box, the Arabic in place (Musa عَلَيْهِ السَّلَامُ).
* **Companions**: at the first mention in each story, `رَضِيَ اللَّهُ عَنْهُ` (عَنْهَا، عَنْهُمَا، عَنْهُمْ) in Arabic as words, and "(may Allah be pleased with him)" in English. In notes and boxes, at first mention in each entry or box.
* Do not put honorifics inside Quran quotes or inside Ibn al-Muqaffa's original text.
* Wording about prophets stays within what the Quran and sahih sources say. No "sin" or "mistake" in our own voice for a prophet; quote the ayah instead (Yunus: "he called out: there is no god but You ... I have been of the wrongdoers").

## Verb classes (bab), not Form numbers

No "form II", "Form IV" or "Form X" anywhere. Name the bab.

* Three letter verbs (ثلاثي مجرد), by the past and present middle vowels:
  * نَصَرَ يَنْصُرُ: بَابُ نَصَرَ · ضَرَبَ يَضْرِبُ: بَابُ ضَرَبَ · فَتَحَ يَفْتَحُ: بَابُ فَتَحَ
  * سَمِعَ يَسْمَعُ: بَابُ سَمِعَ · حَسِبَ يَحْسِبُ: بَابُ حَسِبَ · كَرُمَ يَكْرُمُ: بَابُ كَرُمَ
* Added letters (ثلاثي مزيد): بَابُ الْإِفْعَالِ (أَفْعَلَ), بَابُ التَّفْعِيلِ (فَعَّلَ), بَابُ الْمُفَاعَلَةِ (فَاعَلَ), بَابُ التَّفَعُّلِ (تَفَعَّلَ), بَابُ التَّفَاعُلِ (تَفَاعَلَ), بَابُ الِانْفِعَالِ (اِنْفَعَلَ), بَابُ الِافْتِعَالِ (اِفْتَعَلَ), بَابُ الِافْعِلَالِ (اِفْعَلَّ), بَابُ الِاسْتِفْعَالِ (اِسْتَفْعَلَ).
* Four letter verbs: بَابُ فَعْلَلَ (وَسْوَسَ، زَلْزَلَ).

Every verb entry in a dictionary (pos فعل ماض) carries two fields:

```yaml
present: يَنْصُرُ
bab: بَابُ نَصَرَ
```

The note may then drop its "Present: ..." sentence. Hollow, defective and doubled verbs keep their bab (قَالَ يَقُولُ: بَابُ نَصَرَ; نَامَ يَنَامُ: بَابُ سَمِعَ; دَعَا يَدْعُو: بَابُ نَصَرَ; رَمَى يَرْمِي: بَابُ ضَرَبَ).

## Grammar terms

Arabic term first, English in brackets at its first use in a box or note:
فَاعِلٌ (doer), مَفْعُولٌ بِهِ (object), مُبْتَدَأٌ (topic), خَبَرٌ (predicate), اسْمُ كَانَ / خَبَرُ كَانَ, اسْمُ إِنَّ / خَبَرُ إِنَّ, حَالٌ, تَمْيِيزٌ, نَعْتٌ / صِفَةٌ (describing word), مُضَافٌ / مُضَافٌ إِلَيْهِ, فِعْلٌ مَاضٍ / مُضَارِعٌ / أَمْرٌ, مَرْفُوعٌ / مَنْصُوبٌ / مَجْرُورٌ / مَجْزُومٌ, حَرْفُ جَرٍّ, ظَرْفٌ, صِفَةٌ مُشَبَّهَةٌ, اسْمُ فَاعِلٍ, اسْمُ مَفْعُولٍ, مَصْدَرٌ, مُضَعَّفٌ (doubled root).
Never "subject" alone: it hides the difference between فاعل and مبتدأ.

## Quran

* Every ayah, wherever it appears (story lines, grammar boxes, tips, notes), is Tanzil text unchanged, inside ﴾ ﴿ in story lines, and carries its reference. Do not shorten an ayah in a way that changes its meaning (8:17 must keep "but Allah threw").
* Example sentences in boxes that are Quran text get the `q` treatment or are marked "(Quran X:Y)".

## Reports

* A hadith or report graded sahih is introduced plainly (قَالَ النَّبِيُّ ﷺ, "al-Bukhari reports"), never with رُوِيَ, which signals weakness.
* Tafsir details are attributed ("Ibn Kathir explains"), not stated as plain fact. Reports with weak chains (asbab al-nuzul included) are introduced with "the tafsir books report".
* Nothing is added inside words the Prophet ﷺ narrates.
