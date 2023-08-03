"""
This add-on is a modification of the Answer Confirmation add-on for Anki.
I do not take credit for any of the original code.

Original add-on:
Answer Confirmation plugin for Anki 2.0 by Albert Lyubarsky
License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html

Color Modification and ancillary improvements by MacMarc
"""
__version__ = "1.5"

from aqt.reviewer import Reviewer
from aqt.utils import *
from aqt import utils
from aqt.qt import *
import aqt
from anki.hooks import wrap

# init configuration
Reviewer.colConfConf = aqt.mw.addonManager.getConfig(__name__)

# custom method for deleting the tooltip, since there were problems
# with the handling of global variables by an add-on
def customCloseTooltip(tooltipLabel):
	if tooltipLabel:
		try:
			tooltipLabel.deleteLater()
		except:
			# already deleted as parent window closed
			pass
		tooltipLabel = None
utils.customCloseTooltip = customCloseTooltip

# modified method to alter the background color of the tooltip label
# xref: 0 left; 1 center; 2 right; 
def tooltipWithColour(msg, color, x=0, y=20, xref=1, period=3000, parent=None, width=0, height=0, centered=False):
	global _tooltipTimer, _tooltipLabel
	class CustomLabel(QLabel):
		silentlyClose = True
		def mousePressEvent(self, evt):
			evt.accept()
			self.hide()
	closeTooltip()
	aw = parent or aqt.mw.app.activeWindow() or aqt.mw
	
	# apply width and height
	styleString1 = "height:100%; height: 100%; background: red;"
	styleString2 = "padding: 8px 13px; text-align: center;"
	
	lab = CustomLabel("""\
<table cellpadding=0 padding=0px style="height:100%; height: 100%;">
<tr>
<td style="padding: 8px 13px; text-align: center;">"""+msg+"""</td>
</tr>
</table>""", aw)
	lab.setFrameStyle(QFrame.Shape.Panel)
	lab.setLineWidth(2)
	lab.setWindowFlags(Qt.WindowType.ToolTip)
	lab.setAlignment(Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter)
	
	# adjust height if user configured custom height
	
	if (width>0):
		lab.setFixedWidth(width)
	if (height>0):
		lab.setFixedHeight(height)
	
	p = QPalette()
	p.setColor(QPalette.ColorRole.Window, QColor(color))
	p.setColor(QPalette.ColorRole.WindowText, QColor("#000000"))
	lab.setPalette(p)
	lab.show()
	lab.move(QPoint(x - int(round(lab.width() * 0.5 * xref, 0)), y))
	
	def handler():
		customCloseTooltip(lab)
	
	t = QTimer(aqt.mw)
	t.setSingleShot = True
	t.timeout.connect(handler)
	t.start(period)
	
	_tooltipLabel = lab

utils.tooltipWithColour = tooltipWithColour

# Save how many answer buttons were displayed before the card has been answered
# in the scheduler, as this important information is lost otherwise

def answerCard_before(filter, reviewer, card) :
	utils.answBtnAmt = reviewer.mw.col.sched.answerButtons(card)
	return filter

aqt.gui_hooks.reviewer_will_answer_card.append(answerCard_before)

# Ancillary answer card method to show the tooltip when user answered a card.
# There have been compatibility issues with other add-ons, which override this method.

def answerCard_after(rev, card, ease) : #rev = reviewer
	# load how many answer buttons were displayed and thus how many 'eases' were selectable
	maxEase = utils.answBtnAmt
	
	# determine the position for the label
	x = rev.colConfConf['x_pos'] + 7 #idk why the offset is needed, but only this brings exact values
	y = rev.colConfConf['y_pos']
	
	# read add-on config
	time = rev.colConfConf['time']
	showInterval = rev.colConfConf['showInterval'] #Whether the new interval should be shown
	x_mode = rev.colConfConf['x_mode']
	y_mode = rev.colConfConf['y_mode']
	width = rev.colConfConf['width']
	height = rev.colConfConf['height']
	
	aw = aqt.mw.app.activeWindow() or aqt.mw
	xref = 0
	
	# apply add-on config
	if (x_mode == "left"):
		x = aw.mapToGlobal(QPoint(x, 0)).x()
	elif (x_mode == "middle"):
		x = aw.mapToGlobal(QPoint(x+int(round(aw.width()/2, 0)), 0)).x()
		xref = 1
	elif (x_mode == "right"):
		x = aw.mapToGlobal(QPoint(x+aw.width(), 0)).x()
		xref = 2
	
	if (y_mode == "top"):
		y = aw.mapToGlobal(QPoint(0, y)).y()
	elif (y_mode == "bottom"):
		y = aw.mapToGlobal(QPoint(0, y+aw.height())).y()
	
	if (x < 0):
		x = 0
	
	if (y < 0):
		y = 0
	
	# create the message that is displayed
	if (ease == 1):
		msg = "Again"
		color = "#FF9999"
	elif (ease == maxEase - 2):
		msg = "Hard"
		color = "#A3A3A3"
	elif (ease == maxEase - 1):
		msg = "Good"
		color = "#99FFA4"
	elif (ease == maxEase):
		msg = "Easy"
		color = "#BBEEFF"
	else:
		# default behavior for unforeseen cases
		tooltip("Error in ColorConfirmation add-on: Couldn't interpret ease")
	
	# add interval info
	if (showInterval):
		numberOfDays = card.ivl
		# Convert to humanized string
		if (numberOfDays <= 30):
			ivl = str(numberOfDays) + " days"
		elif (numberOfDays <= 365):
			ivl = str(round(numberOfDays/30.44, 1)) + " months"; # convert days to months
		else:
			ivl = str(round(numberOfDays/365.2425, 1)) + " years"; # convert days to years
		
		msg = msg + "<br/><b>" + ivl + "</b>"
	
	# show tooltip
	try:
		tooltipWithColour(msg, color, x=x, y=y, xref=xref, period=time, width=width, height=height)
	except NameError:
		tooltip(msg)

#Reviewer._answerCard  = wrap(Reviewer._answerCard, answerCard_before, "before")
Reviewer.CustomAnswerCard = answerCard_after #only for compatibility with other add-ons, that override this method
Reviewer._answerCardAfter = answerCard_after

aqt.gui_hooks.reviewer_did_answer_card.append(answerCard_after)