# -*- coding: utf-8 -*-

"""
Copyright 2023 @ Evandro Coan
Anki Addon to bury related siblings sources

Redistributions of source code must retain the above
copyright notice, this list of conditions and the
following disclaimer.

Redistributions in binary form must reproduce the above
copyright notice, this list of conditions and the following
disclaimer in the documentation and/or other materials
provided with the distribution.

Neither the name Evandro Coan nor the names of any
contributors may be used to endorse or promote products
derived from this software without specific prior written
permission.

This program is free software; you can redistribute it and/or modify it
under the terms of the GNU General Public License as published by the
Free Software Foundation; either version 3 of the License, or ( at
your option ) any later version.

This program is distributed in the hope that it will be useful, but
WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the GNU
General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
"""

import aqt

from typing import Any

from aqt import gui_hooks, CallingFunction
from aqt.webview import AnkiWebView
from aqt.webview import WebContent

from aqt.qt import (
    qtmajor,
    qtminor,
)

from aqt import mw
mw.addonManager.setWebExports(__name__, r"web/ankimedia.js")

from anki.cards import Card


def enable_javascript_playback(web: AnkiWebView) -> None:
    page_settings = web._page.settings()

    if qtmajor > 5 and qtminor > 1:
        page_settings.setAttribute(
            aqt.PyQt6.QtWebEngineCore.QWebEngineSettings.WebAttribute.PlaybackRequiresUserGesture,
            False,
        )
    elif qtmajor == 5 and qtminor >= 11:
        page_settings.setAttribute(
            aqt.QWebEngineSettings.PlaybackRequiresUserGesture, False  # type: ignore
        )


def webview_will_set_content(web_content: WebContent, context: Any):
    addon_package = mw.addonManager.addonFromModule(__name__)
    web_content.js.insert(0, f"/_addons/{addon_package}/web/ankimedia.js")


def webview_did_init(web_content: WebContent, location: CallingFunction):
    # print(f'webview_did_init {location}, web {web_content}.')

    if location in (CallingFunction.CLAYOUT, CallingFunction.PREVIWER, CallingFunction.MAIN_WINDOW):
        enable_javascript_playback(web_content)
    else:
        print(f'ankimediaqueue, invalid location {location}, web {web_content}.')


def card_will_show_state(text: str, card: Card, kind: str, web_content: WebContent, skip_front: bool, has_autoplayed: bool):
    # print(f'card_will_show_state skip_front {skip_front}, autoplay {card.autoplay()}, has_autoplayed {has_autoplayed}, web {web_content}.')

    if skip_front:
        web_content.eval("ankimedia.skip_front = true;")

    if not has_autoplayed:
        web_content.eval(f"ankimedia._reset({{skip_front_reset: {'true' if skip_front else 'false'}}});")

    if not card.autoplay():
        web_content.eval("ankimedia.autoplay = false;")

    return text


def audio_will_toggle(web_content: WebContent):
    # print(f'audio_will_toggle web {web_content}.')
    web_content.eval("ankimedia.togglePause();")


def audio_will_replay(web_content: WebContent, card: Card, state: str):
    # print(f'audio_will_replay state {state}, replay_question_audio_on_answer_side {card.replay_question_audio_on_answer_side()}, web {web_content}.')

    if state == "answer" and not card.replay_question_audio_on_answer_side():
        web_content.eval("ankimedia.skip_front = true;")

    web_content.eval("ankimedia.replay();")


def show_both_sides_will_toggle(web_content: WebContent,  card: Card, state: str, toggle: bool):
    # print(f'show_both_sides_will_toggle state {state}, toggle {toggle}, web {web_content}.')
    web_content.eval("ankimedia._reset();")

    if state == "question" and toggle:
        web_content.eval("ankimedia.skip_front = true;")


gui_hooks.webview_did_init.append(webview_did_init)
gui_hooks.card_will_show_state.append(card_will_show_state)
gui_hooks.audio_will_toggle.append(audio_will_toggle)
gui_hooks.audio_will_replay.append(audio_will_replay)
gui_hooks.show_both_sides_will_toggle.append(show_both_sides_will_toggle)
gui_hooks.webview_will_set_content.append(webview_will_set_content)
