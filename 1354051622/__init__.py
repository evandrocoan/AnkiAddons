# -*- coding: utf-8 -*-
# Author:  Albert Lyubarsky
# Email: albert.lyubarsky@gmail.com
# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html
#
#   Answer Confirmation plugin for Anki 2.0
__version__ = "1.0.0"


from aqt.reviewer import Reviewer
from aqt.utils import tooltip
from anki.hooks import wrap


def answerCard_before(self, ease) :
	l = self._answerButtonList()
	a = [item for item in l if item[0] == ease]
	if len(a) > 0 :
		tooltip(a[0][1])
		

Reviewer._answerCard  = wrap(Reviewer._answerCard, answerCard_before, "before")
