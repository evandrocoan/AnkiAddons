# -*- coding: utf-8 -*-

"""
Copyright 2020 @ Evandro Coan
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

from anki import hooks

from anki.utils import stripHTML
from anki.consts import QUEUE_TYPE_REV
from anki.consts import QUEUE_TYPE_NEW


def _getSource(field, note):
    try:
        return note[field]
    except KeyError:
        pass


def getSource(card):
    note = card.note()
    source = _getSource("Source", note) or _getSource("source", note)
    return stripHTML(source) if source else None


def bury_related_sources(card, toBury, scheduler):
    firstsource = getSource(card)

    if scheduler._burySiblingsOnAnswer and firstsource:
        for cid, queue in scheduler.col.db.execute(
            f"""
select id, queue from cards where nid!=? and id!=?
and (queue={QUEUE_TYPE_NEW} or (queue={QUEUE_TYPE_REV} and due<=?))""",
            card.nid,
            card.id,
            scheduler.today,
        ):
            source = getSource(scheduler.col.getCard(cid))

            if source and source == firstsource and len(firstsource) > 0:
                toBury.append(cid)

    # print(f'Burying {toBury}...')


hooks.scheduler_did_bury_siblings_notes.append(bury_related_sources)

