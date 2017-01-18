#!/usr/bin/env python3

import sys
import os
import time
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess

class WatchAndSync(FileSystemEventHandler):
	def __init__(self, local_file, remote_file):
		self.local_file = local_file
		self.remote_file = remote_file

		self.observer = Observer(timeout=.1)
		self.observer.schedule(self, os.path.abspath(os.path.dirname(local_file)))

	def sync(self):
		print("iniating upload")
		subprocess.run(['rsync', self.local_file, self.remote_file])
		print("finished upload")


	def on_change(self, path):
		print('what is path? ' + str(path))
		self.sync()

	def on_create(self, event):
		print("in on create")
		if self.observer.__class__.__name__ == 'InotifyObserver':
			return

		else:
			self.on_change(event.src_path)

	def on_modified(self, event):
		print('event is', event)
		self.on_change(event.src_path)

	def on_moved(self, event):
		print('in on moved, event is', event)
		self.observer.stop()
		self.observer.join()
		exit(1)

	def run(self):
		print("about to start")
		self.observer.start()
		try:
			while True:
				time.sleep(3600)
		except KeyboardInterrupt:
			self.observer.stop()
		self.observer.join()


def main():
	was = WatchAndSync(sys.argv[1], sys.argv[2])
	try:
		print("about to run")
		was.run()
	except KeyboardInterrupt:
		print()
		exit(0)

if __name__ == '__main__':
	main()