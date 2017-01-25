Plugin for CudaText.
Creates backup copy of current file: a) by command in Plugins, b) by auto-creation on file saving.

Also gives command to call file-compare: current text, and previous backup copy.
For compare, it calls diff (Unix) or WinMerge (Windows).

Filename of copy - customizable via templates. Templates have macros for year/month/day/hours/etc, and
macros for parts of filename. See the help text, by pressing Help button in Config dialog.
Has macros for number counter, for upper/lower case. 


Author: Andrey Kvichanskiy (kvichans, at forum/github)
License: MIT
