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

Run `language-practice path/to/toml/file.toml` to start the program. This may take
some time if you are using conjugation or declension charts as it will pull them in
parallel from the internet. An internet connection is only required for this part
of the execution.

Command line options:
* `--traceback`: useful for bug reporting, bubbles the Python exception up to the
terminal
* `--reset`: Redownload the entire cache and current information about what words you
have guessed correctly/incorrectly

Run ctrl-C to exit the program and save your progress

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

## Commands

Type:

* e to show the initial side of the flashcard you first saw with the word in your
language
* d to show the the word in the language you are studying
* y to mark a word as correctly recalled
* n to mark a word as incorrectly recalled
* c to see the declension or conjugation chart 
* u to see usage information
* r to refresh the downloaded cache for the current entry

## Spaced repetition

This app will show you words you get right less and less frequently and words you get
wrong more and more frequently until you get them right.

The exact algorithm is rather simple and could potentially be improved.

`num_right` is number of times guessed correctly.

`num_wrong` is number of times guessed incorrectly.

`num_wrong_since` is the number of times you have gotten it wrong since 10 correct
answers. This is used to balance out words that you sometimes get correct and sometimes
get incorrect to keep it in less frequent but current rotation until you consistently
guess it right.

`num_right` and `num_wrong` are mutally exclusive. If one is non-zero, the other will
be set to zero.

The card will be repeated `n` cards later where `n` is
`num_right * max(15 - num_wrong_since, 1)` or `max(15 - num_wrong, 1)`.

# Contributing

Please open bugs and request features on Github! I would love to make this more useful
to others.
