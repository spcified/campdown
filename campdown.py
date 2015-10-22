#!/usr/bin/env python

import re
import os
import math
import sys
import requests
import json

# Downloads a supplied file from a response.
def download_file(url, folder, name):
	# Get the size of the remote file.
	full_response = requests.get(url, stream = True)
	total_length = full_response.headers.get('content-length')

	# Open a file stream which will be used to save the output string
	with open(folder + "/" + re.sub('[\\/:*?<>|]', "", name) + ".mp3", "wb") as f:
		# Make sure that the printed string is compatible with the user's command line. Else, encode.
		# This applies to all other print arguments throughout this file.
		try:
			print('Downloading: %s' % name)
			
		except UnicodeEncodeError:
			try:
				print('Downloading: %s' % name.encode(sys.stdout.encoding, errors = "replace").decode())

			except UnicodeDecodeError:
				print('Downloading: %s' % name.encode(sys.stdout.encoding, errors = "replace"))

		# If the file is empty simply write out the returned content from the request.
		if total_length is None:
			f.write(full_response.content)

		else:
			# Storage variables used while evaluating the already downloaded data.
			dl = 0
			total_length = int(total_length)
			cleaned_length = int((total_length * 100) / pow(1024, 2)) / 100
			block_size = 2048

			try:
				for i in range(math.ceil(total_length / 1048576)):
					response = requests.get(url, headers = {'Range': 'bytes=' + str(i * 1048576) + "-" + str((i + 1) * (1048576) - 1)}, stream = True)

					for chunk in response.iter_content(chunk_size = block_size):
						# Add the length of the chunk to the download size and write the chunk to the file.
						dl += len(chunk)
						f.write(chunk)

						# Display a loading bar based on the currently download filesize.
						done = int(50 * dl / total_length)
						sys.stdout.write("\r[%s%s%s] %sMB / %sMB " % ('=' * done, ">", ' ' * (
							50 - done), (int(((dl) * 100) / pow(1024, 2)) / 100), cleaned_length))
						sys.stdout.flush()

			except(KeyboardInterrupt):
				# Close the filestream and remove the unfinished file if the user interrupts the download process.
				f.close()
				print('\nKeyboardInterrupt caught - skipping track')
				os.remove(folder + "/" + name + ".mp3")

	# Insert a new line for formatting-OCD's sake.
	print('\n')

# Check that this file's main function is not being called from another file.
if __name__ == "__main__":
	try:
		# Fetch the program arguments and make sure that they are valid.
		try:
			bandcamp_url = sys.argv[1].replace('"', '')

		except:
			print('\nMissing required URL argument')
			sys.exit(2)

		if not "http://" in bandcamp_url and not "https://" in bandcamp_url:
			print('\n%s is not a valid URL' % bandcamp_url)
			sys.exit(2)

		try:
			# Make sure that the output folder has the right path syntax
			outputfolder = sys.argv[2].replace('\\', '/')

			# Check if the path is relative or absolute. If relative, make it absolute.
			if outputfolder[-1] != "/": outputfolder = str(outputfolder) + "/"
			
			if not os.path.isabs(outputfolder):
				if not os.path.exists(os.path.split(os.path.abspath(__file__).replace('\\', '/'))[0] + "/" + outputfolder):
					os.makedirs(os.path.split(os.path.abspath(__file__).replace('\\', '/'))[0] + "/" + outputfolder);

				outputfolder = os.path.split(os.path.abspath(__file__).replace('\\', '/'))[0] + "/" + outputfolder

		except:
			# If no path is specified revert to the absolute path of the main file.
			outputfolder = os.path.split(os.path.abspath(__file__).replace('\\', '/'))[0] + "/"

		# Get the content from the supplied Bandcamp page
		try:
			r = requests.get(bandcamp_url).content.decode('utf-8')

		except:
			print("An error occurred while trying to access your supplied URL")
			exit()

		# Retrieve the base page URL, fetch the album art URL and create variables which will be used later on.
		bandcamp_base_url = str(bandcamp_url).split("/")[0] + "//" + str(bandcamp_url).split("/")[2]
		bandcamp_art_url = str(r).split('<a class="popupImage" href="', 1)[1].split('">')[0]
		bandcamp_isAlbum = False
		bandcamp_queue = []
		bandcamp_artist = ""

		# Find the artist name of the supplied Bandcamp page.
		try:
			bandcamp_artist = str(r).split("var BandData = {", 1)[1].split("}")[0].split('name : "')[1].split('",')[0]

		except IndexError:
			try:
				bandcamp_artist = str(r).split("var BandData = {", 1)[1].split("}")[0].split('name: "')[1].split('",')[0]

			except:
				print("\nFailed to fetch the band title")

		# We check if the page has a track list or not. If not, we only fetch the track info for the one track on the given Bandcamp page.
		if str(r).find("track_list") == -1:
			# Extract the unformatted JSON array from the request's content. Convert it to an actual Python array afterwards.
			rawinfo = ("{" + (str(r).split("trackinfo: [{", 1)[1].split("}]")[0]) + "} ")
			trackinfo = json.loads(rawinfo)

			# Insert the track data into the queue and inform the downloader that it's not an album.
			bandcamp_queue.insert(1, trackinfo)
			bandcamp_isAlbum = False

			# Add the name of the album this single track might belong to, to the information that will make up the output filename. 
			try:
				bandcamp_album = str(r).split(
					'<span itemprop="name">')[1].split("</span>")[0]

			except IndexError:
				bandcamp_album = ""

		else:
			# Since the supplied URL was detected to be an album URL, we extract the name of the album.
			bandcamp_isAlbum = True
			bandcamp_album = re.sub('[:*?<>|]', '', str(r).split('<meta name="Description" content=')[1].split(" by ")[0][2:])

			# Create a new album folder if it doesn't already exist.
			if not os.path.exists(outputfolder + "/" + bandcamp_artist + " - " + bandcamp_album + "/"):
				try:
					print('\nCreated album folder in %s%s - %s%s' %(outputfolder, bandcamp_artist, bandcamp_album, "/"))

				except UnicodeEncodeError:
					try:
						print('\nCreated album folder in %s%s - %s%s' %(outputfolder, bandcamp_artist.encode(sys.stdout.encoding, errors = "replace").decode(),
							bandcamp_album.encode(sys.stdout.encoding, errors = "replace").decode(), "/"))

					except UnicodeDecodeError:
						print('\nCreated album folder in %s%s - %s%s' %(outputfolder, bandcamp_artist.encode(sys.stdout.encoding, errors = "replace"),
							bandcamp_album.encode(sys.stdout.encoding, errors = "replace"), "/"))

				os.makedirs(outputfolder + "/" + bandcamp_artist + " - " + bandcamp_album + "/")

			# Extract the string of tracks from the request's response content. Convert the individual titles to single entries for use in an array.
			bandcamp_album_tracktable = str(r).split('<table class="track_list track_table" id="track_table">', 1)[1].split('</table>')[0]
			bandcamp_album_tracks = bandcamp_album_tracktable.split("<tr")

			# Iterate over the tracks found and begin traversing the given track's title information.
			print('\nListing found tracks')

			for i, track in enumerate(bandcamp_album_tracks):
				position = track.find('<a href="/track')

				if position != -1:
					# Find the track's name.
					position = position + len('<a href="/track')
					trackname = ""

					while track[position] != '"':
						trackname = trackname + track[position]
						position = position + 1

					if trackname != "":
						print(bandcamp_base_url + "/track" + trackname)

						# Make a single request to the track's own URL and extract the track info from there.
						track_r = requests.get(bandcamp_base_url + "/track" + trackname).content.decode('utf-8')
						rawinfo = ("{" + (str(track_r).split("trackinfo: [{", 1)[1].split("}]")[0]) + "} ")
						trackinfo = json.loads(rawinfo)

						# Insert the acquired data into the queue. 
						bandcamp_queue.insert(i, trackinfo)

		if bandcamp_isAlbum:
			# Since we know that the downloader is fetching an album we might as well sum up the output string for easier encoding.
			outputfolder = outputfolder + bandcamp_artist + " - " + bandcamp_album
		
		# Once again differentiating between and encoded output folder string and the normal string to avoid command line encoding errors.
		try:
			print('\nWriting all output files to %s\n' %outputfolder)

		except UnicodeEncodeError:
			try:
				print('\nWriting all output files to %s\n' %outputfolder.encode(sys.stdout.encoding, errors = "replace").decode())

			except UnicodeDecodeError:
				print('\nWriting all output files to %s\n' %outputfolder.encode(sys.stdout.encoding, errors = "replace"))
		
		# Start the process of downloading files from the queue.
		for i in range(0, len(bandcamp_queue)):
			# Get the title of the current queue-item.
			title = bandcamp_queue[i]["title"]

			# Create beautiful track name formatting. This makes the output filename look good.
			if title.find(" - ") != -1:
				partialtitle = str(title).split(" - ", 1)

				if bandcamp_isAlbum:
					title = partialtitle[0] + " - " + bandcamp_album + " - " + str(i + 1) + " " + partialtitle[1]

				else:
					title = partialtitle[0] + " - " + bandcamp_album + " - " + partialtitle[1]
			else:
				if bandcamp_isAlbum:
					title = bandcamp_artist + " - " + bandcamp_album + " - " + str(i + 1) + " " + title

				else:
					title = bandcamp_artist + " - " + bandcamp_album + " - " + title

			try:
				# Retrieve the MP3 file URL from the queue-item.
				url = bandcamp_queue[i]["file"]["mp3-128"]

				# Add in http for those times when Bandcamp is rude.
				if url[:2] == "//":
					url = "http:" + url

			except TypeError:
				# If this is not possible, the desired file is not openly available.
				try:
					print('\n' + title + " is not openly available - skipping track")

				except UnicodeEncodeError:
					try:
						print('\n%s%s' %(title.encode(sys.stdout.encoding, errors = "replace").decode(), " is not openly available - skipping track"))

					except UnicodeDecodeError:
						print('\n%s%s' %(title.encode(sys.stdout.encoding, errors = "replace"), " is not openly available - skipping track"))
				continue

			# print("REQUEST LENGTH: " +(requests.get(url, stream = True).headers.get('content-length')) +" || FILE LENGTH: " +str(os.path.getsize(outputfolder + "/" + title + ".mp3")))

			# Check if the file doesn't exist and download it.
			if os.path.isfile(outputfolder + "/" + title + ".mp3") == False:
				# if "string" in title: - Filter out tracks with a certain tag.
				download_file(url, outputfolder, title)

			# Inspect the already existing file's size and overwrite it, if it's smaller than the remote file.
			elif os.path.getsize(outputfolder + "/" + title + ".mp3") < int(requests.get(url, stream = True).headers.get('content-length')):
				print('\nRedownloading since the file size doesn\'t match up.')
				download_file(url, outputfolder, title)

			else:
				try:
					print('\nFile found - skipping %s' % title)

				except UnicodeEncodeError:
					try:
						print('\nFile found - skipping %s' % title.encode(sys.stdout.encoding, errors = "replace").decode())

					except UnicodeDecodeError:
						print('\nFile found - skipping %s' % title.encode(sys.stdout.encoding, errors = "replace"))
				
		print('\nFinished downloading all tracks')
		
		# Download the album art if the supplied URL was an album URL.
		if bandcamp_isAlbum:
			try:
				print('\nDownloading album art...')

				# Make an image request to the art URL we extracted at the very start.
				image_request = requests.get(bandcamp_art_url, stream = True)

				# Make sure that the album art actually exists. Write it to a file then.
				if image_request.status_code == 200:
					with open(outputfolder + "/cover" + bandcamp_art_url[-4:], 'wb') as f:
						for chunk in image_request.iter_content(1024):
							f.write(chunk)

			# Remove the corrupt file if the user interrupted the download process.
			except (KeyboardInterrupt, SystemExit):
				print('\n\nDownload aborted - removing download remnants')
				os.remove(outputfolder + "/cover" + bandcamp_art_url[-4:])

				sys.exit(2)
			try:
				print('Saved album art to %s%s%s' %(outputfolder, "/cover", bandcamp_art_url[-4:]))

			except UnicodeEncodeError:
				try:
					print('Saved album art to %s%s%s' %(outputfolder.encode(sys.stdout.encoding, errors = "replace").decode(), "/cover", bandcamp_art_url[-4:]))
					
				except UnicodeDecodeError:
					print('Saved album art to %s%s%s' %(outputfolder.encode(sys.stdout.encoding, errors = "replace"), "/cover", bandcamp_art_url[-4:]))

	except (KeyboardInterrupt):
		print("Double interrupt caught - exiting program...")
		sys.exit(2)