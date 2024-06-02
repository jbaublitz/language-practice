# 0.2.1

## Bug fixes
* Fixed bug in directory feature

# 0.2.0

## Enhancements
* Ability to specify a directory as the source of the flashcard files

## Breaking changes
* Word file is no longer a positional argument

# 0.1.5

## Bug fixes
* Bug fix to remove word from repetition.json file if it is removed from the .toml
file. Previously, this would result in shutdown of the application.

# 0.1.4

## Improvements
* Add support for custom inflection tables.

# 0.1.3

## Bug fixes
* Fix bug where Ukrainian charts were only pulled for the refresh command
and not at start up.
