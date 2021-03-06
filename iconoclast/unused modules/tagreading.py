from mutagen.mp3 import MP3
from mutagen.id3 import ID3
from mutagen.mp4 import MP4
from mutagen.oggvorbis import OggVorbis
from mutagen.flac import FLAC
from mutagen.asf import ASF

from os.path import splitext

class TrackMetaData:
	def getTrackType(self, filepath):
		fileExtension = splitext(filepath.lower())[1]
		if fileExtension == '.ogg' or fileExtension == '.oga':
			return self.oggInfo(filepath)
		elif fileExtension == '.mp4' or fileExtension == '.m4a':
			return self.m4aInfo(filepath)
		elif fileExtension == '.mp2' or fileExtension == '.mp3':
			return self.id3Info(filepath)
		elif fileExtension == '.flac':
			return self.flacInfo(filepath)
		elif fileExtension == '.wma':
			return self.wmaInfo(filepath)
		else:
			print "not a valid file extension!"
			return False
		
	def id3Info(self, filepath):
		audio = ID3(filepath)

		try: tracknum = audio["TRCK"][0]
		except: tracknum = None
		if tracknum is not None:
			try:    tracknum = int(tracknum.split('/')[0])
			except: tracknum = int(tracknum)
		try: songtitle = audio["TIT2"][0]
		except: songtitle = None
		try: artist = audio["TPE1"][0]
		except: artist = None
		try: album = audio["TALB"][0]
		except: album = None
		try: genre = audio["TCON"][0]
		except: genre = None

		tracklength = int(round(MP3(filepath).info.length))
		m,s = divmod(tracklength, 60)
		tracklength = "%02i:%02i" %(m,s)

		return [tracknum, songtitle, artist, album, tracklength, genre, filepath]

	def m4aInfo(self, filepath):
		audio = MP4(filepath)

		try: tracknum = audio["trkn"][0][0]
		except: tracknum = None
		if tracknum is not None:
			try:    tracknum = int(tracknum.split('/')[0])
			except: tracknum = int(tracknum)
		try: songtitle = audio["\xa9nam"][0]
		except: songtitle = None
		try: artist = audio["\xa9ART"][0]
		except: artist = None
		try: album = audio["\xa9alb"][0]
		except: album = None
		try: genre = audio["\xa9gen"][0]
		except: genre = None

		tracklength = int(round(audio.info.length))
		m,s = divmod(tracklength, 60)
		tracklength = "%02i:%02i" %(m,s)

		return [tracknum, songtitle, artist, album, tracklength, genre, filepath]

	def oggInfo(self, filepath):
		audio = OggVorbis(filepath)

		try: tracknum = audio["tracknumber"][0] 
		except: tracknum = None
		if tracknum is not None:
			try:    tracknum = int(tracknum.split('/')[0])
			except: tracknum = int(tracknum)
		try: songtitle = audio["title"][0]
		except: songtitle = None
		try: artist = audio["artist"][0]
		except: artist = None
		try: album = audio["album"][0]
		except: album = None
		try: genre = audio["genre"][0]
		except: genre = None

		tracklength = int(round(audio.info.length))
		m,s = divmod(tracklength, 60)
		tracklength = "%02i:%02i" %(m,s)

		return [tracknum, songtitle, artist, album, tracklength, genre, filepath]

	def flacInfo(self, filepath):
		audio = FLAC(filepath)

		try: tracknum = audio["tracknumber"][0] 
		except: tracknum = None
		if tracknum is not None:
			try:    tracknum = int(tracknum.split('/')[0])
			except: tracknum = int(tracknum)
		try: songtitle = audio["title"][0]
		except: songtitle = None
		try: artist = audio["artist"][0]
		except: artist = None
		try: album = audio["album"][0]
		except: album = None
		try: genre = audio["genre"][0]
		except: genre = None

		tracklength = int(round(audio.info.length))
		m,s = divmod(tracklength, 60)
		tracklength = "%02i:%02i" %(m,s)

		return [tracknum, songtitle, artist, album, tracklength, genre, filepath]

	def wmaInfo(self, filepath):
		audio = ASF(filepath)

		try: tracknum = audio["WM/TrackNumber"][0]
		except: tracknum = None
		if tracknum is not None:
			try:    tracknum = int(tracknum.split('/')[0])
			except: tracknum = int(tracknum)
		try: songtitle = str(audio["Title"][0])
		except: songtitle = None
		try: artist = str(audio["Author"][0])
		except: artist = None
		try: album = str(audio["WM/AlbumTitle"][0])
		except: album = None
		try: genre = str(audio["WM/Genre"][0])
		except: genre = None

		tracklength = int(round(audio.info.length))
		m,s = divmod(tracklength, 60)
		tracklength = "%02i:%02i" %(m,s)

		return [tracknum, songtitle, artist, album, tracklength, genre, filepath]

#getmesumdatabruv = TrackMetaData()
#print(getmesumdatabruv.getTrackType("/media/Media/Music/Carlos Santana/Playin With Carlos/02-carlos_santana-too_late_too_late_(feat_gregg_rolie).mp3"))
