#!/usr/bin/env python3
# © Copyright 2013 axujen, <axujen at gmail.com>. All Rights Reserved.
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.

"""This is a script to randomly select an album in the current mpd playlist."""

import random
import argparse

try:
	import mpd
except ImportError:
	print('You must install the python-mpd2 library. You can get it from: '\
			'https://pypi.python.org/pypi?:action=display&name=python-mpd2')
	raise SystemExit

# Default Server info, change these values to match yours.
HOST='127.0.0.1'
PORT='6600'
PASSWORD=None

class Client(mpd.MPDClient):
	"""Client that connects and communicates with the mpd server."""

	def __init__(self, server_id, password=False):
		mpd.MPDClient.__init__(self)
		self.connect(**server_id)
		if password:
			self.password(password)

	def getalbums(self):
		"""Grab a list of the albums in the playlist."""
		playlist = self.playlistinfo()
		albums = {}
		for song in playlist:
			album = song['album']
			if not album in albums:
				albums[album] = [song]
			else:
				albums[album].append(song)

		return albums

	def getcurrent_album(self):
		"""Get the current playing album."""
		return self.currentsong()['album']

	def random_album(self, albums):
		"""Get a random album from the albums dictionary."""
		albums = list(albums.keys())
		# Everything except the current playing album
		current_album = self.getcurrent_album()
		albums.pop(albums.index(current_album))
		return random.choice(albums)

	def play_album(self, album):
		"""Play the first song in the given album."""
		id = album[0]['id']
		self.playid(id)

	def play_random(self, albums=None):
		"""Play a random album from the list of albums."""
		if not albums:
			albums = self.getalbums()

		toplay = self.random_album(albums)
		self.play_album(albums[toplay])

	def atlast_song(self):
		albums = self.getalbums()
		album = albums[self.getcurrent_album()]
		last_song = album[-1]['id']
		cursong = self.currentsong()['id']
		return True if last_song == cursong else False

	def idleloop(self):
		"""Loop for daemon mode."""
		albums = self.getalbums()
		while True:
			album = self.getcurrent_album()
			reasons = self.idle('playlist', 'player')
			if 'playlist' in reasons:
				albums = self.getalbums() # refresh albums
				continue
			elif 'player' in reasons:
				if self.atlast_song():
					self.idle('player')
					if self.getcurrent_album() != album:
						self.play_random(albums)
				else:
					continue

	def __del__(self):
		"""Close client after exiting."""
		self.close()


## Arguments
arguments = argparse.ArgumentParser()
arguments.add_argument('-d', '--daemon', action='store_true', dest='daemon',
		help='run the script in daemon mode.', default=False)
arguments.add_argument('-p', '--port', dest='port', default=PORT,
		help='specify mpd\'s port (defaults to {})'.format(PORT), metavar='PORT')
arguments.add_argument('-u', '--host', dest='host', default=HOST,
		help='specify mpd\'s host (defaults to {})'.format(HOST), metavar='HOST')
arguments.add_argument('--password', dest='password', default=PASSWORD,
		help='specify mpd\'s password', metavar='PASSWORD')

if __name__ == '__main__':
	args = arguments.parse_args()
	SERVER_ID = {"host":args.host, "port":args.port}
	client = Client(SERVER_ID, args.password)
	if args.daemon:
		try:
			client.idleloop()
		except KeyboardInterrupt:
			raise SystemExit # No need for the ugly traceback when interrupting.
	else:
		client.play_random()
