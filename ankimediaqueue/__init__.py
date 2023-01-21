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

from aqt import gui_hooks
from aqt.webview import AnkiWebView
from aqt.webview import WebContent

from aqt.qt import (
    qtmajor,
    qtminor,
)

from aqt import mw
mw.addonManager.setWebExports(__name__, r"web/ankimedia.js")


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


def on_ankimediaqueue(web: AnkiWebView, location: str):
    # print(f'location {location}, web {web}.')

    if location == 'autoplay':
        web.eval("ankimedia.autoplay = false;")

    elif location == 'toggle':
        web.eval("ankimedia.togglePause();")

    elif location == 'reset':
        web.eval("ankimedia._reset();")

    elif location == 'reset_skip':
        web.eval("ankimedia._reset({skip_front_reset: true});")

    elif location == 'skip':
        web.eval("ankimedia.skip_front = true;")

    elif location == 'replay':
        web.eval("ankimedia.replay();")

    elif location == 'enable':
        enable_javascript_playback(web)

    else:
        print(f'ankimediaqueue, invalid location {location}, web {web}.')


def on_webview_will_set_content(web_content: WebContent, context: Any):
    addon_package = mw.addonManager.addonFromModule(__name__)
    web_content.js.insert(0, f"/_addons/{addon_package}/web/ankimedia.js")


gui_hooks.will_show_web.append(on_ankimediaqueue)
gui_hooks.webview_will_set_content.append(on_webview_will_set_content)
