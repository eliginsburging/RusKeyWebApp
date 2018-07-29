# RusKeyWebApp
RusKey is an open source quizlet to help people learn Russian. The basic premise was simple:
- [Scrape](https://github.com/eliginsburging/RuskeyVerbScraper/blob/master/RusKeyDataScrape.py) data from an [open source Russian dictionary](https://en.openrussian.org/) with a verb frequency list.
- [Send](https://github.com/eliginsburging/RuskeyVerbScraper/blob/master/PollyPull.py) that data to Amazon's Polly text to speech service for Russian audio.
- Create a quiz program in Django based on the text and audio.

Note that this repository only contains the code for the third bullet point above.

## Basics
After a user logs in, they are presented with a list of verbs. These are sorted by due date (for any verbs with examples that the user has already studied) and then by frequency number. If the user clicks on a verb in the list, they see a verb detail page with conjugation information, example sentences, and audio. From there, the user can launch the quiz functionality.

### Quiz Process
Each quiz covers 3 examples associated with the given verb. The app is configured to test the user on unstudied examples first. Once all examples have been studied, it selects the next exmaples for study based on due date (using the [SM2 algorithm](https://www.supermemo.com/english/ol/sm2.htm)). For each example included in the quiz, the user is presented with one introductory flashcard with both the  example and its translation (if the user has never studied the example before) and then four quiz types:
- multiple choice fill in the blank
- typed fill in the blank
- arrange all the words in the sentence
- reproduce the entire sentence

If the user performs poorly on any of the quizes, they will be required to type the correct answer (the missing word for fill in the blank quizzes or the whole sentence for the other quizzes) before continuing. Once the user has completed all four quizes for each of the three examples, they are presented with a quiz summary page which provides information on their performance.

## Notes and Caveats
- All examples and verbs in the program should be properly stressed.
- At present, scoring is based solely on the fuzzywuzzy string comparison library. This is not a very sophisticated method, but it sort of works.
- Answers are case sensitive, but do not require marked stress (if you know of a way to mark stresses easily in a Russian keyboard layout, please let me know).
- At present, this project is configured to run on Heroku using Amazon S3 storage for static files.
- Performance data is stored on a per example basis, but is exposed to the user on a per verb basis (the most overdue example dictates the due date of the verb).
- Quiz scores for each example are averaged across the 4 quiz types and are only updated in the db upon completion of the fourth quiz type for a given example.

## Acknowledgements
I built the bulk of this application as part of the Chicago Python Users Group (Chipy) [Mentorship Program](https://chipymentor.org/). If you live in Chicago and you like Python, I would highly recommend both Chipy's monthly meetings and their free mentorship program. My mentor Steve gave me a lot of good advice over the course of this project.
