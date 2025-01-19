# `language_practice`

Flashcard terminal app with spaced repetition

## Languages supported

While any language with gender or verb aspect can be used, declension/verb conjugation
charts are currently only supported for Ukrainian, Russian and French.

## Installing

### Minimum Python version
This application relies heavily on the TOML format so Python 3.11 is the minimum
supported Python version.

### Pip 
Run `pip install --user language-practice`.

### From source
Download the repo and run `pip install --user .` in the top level of the repo.

# Running the program

Run `language-practice` to start the program.

## File format

The file format is TOML. 

### Top level options

* `lang`: Accepts `uk`, `ru` and `fr` as values if you would like to pull conjugation
or declension charts from Wiktionary. Not specifying this value does not pull charts
and runs in flashcard-only mode.

### Words

Put each word under a `[[words]]` heading.

Supported keys are:
* `word`: **required**, vocabulary word to learn in another language
* `definition`: **required**, definition of the vocabulary to learn in your language,
this will be displayed to you for you to guess the word to help recall
* `aspect`: aspect of the verb, displayed with the definition to differentiate between
perfective and imperfective verbs if the language you know does not have them
* `usage`: arbitrary usage note about the word entry
* `part_of_speech`: used to differentiate between relational adjectives and nouns and
similar cases where the part of speech is not clear in your language from the word
itself
* `charts`: add custom inflection chart where not available on Wiktionary
* `gender`: gender of the word, displayed with the word to be studied

## Spaced repetition

This app uses SuperMemo 2 for spaced repetition.

# Contributing

Please open bugs and request features on Github! I would love to make this more useful
to others. Usability issues are always appreciated.
