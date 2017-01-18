#!/usr/bin/env python3

import sys
import os
import time
import argparse
import resource
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
import subprocess


parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', action='store_true', help='Print whenever a transfer (upload) '
                                                                 'has been initiated/completed')
parser.add_argument('-d', '--daemonize', action='store_true', help='Instead of running in the local terminal '
                                                                   'make the process into a daemon. This will '
                                                                   'overwrite verbosity')
parser.add_argument('local_file', help="The local file to watch and transfer")
parser.add_argument('remote_file', help="The remote file to be updated to the local_file")
args = parser.parse_args()


def daemonize():
    UMASK = 0
    LOGDIR = '/tmp/'
    MAXFD = 1024
    """
        Creates the actual daemon by double forking which
        disconnects from the terminal and makes the program into an entirely new process
        :return: 0 for success
        """
    try:
        pid = os.fork()
    except OSError as e:
        raise Exception("{} [{}]".format(e.strerror, e.errno))

    if pid == 0:  # if we are the child
        os.setsid()  # set the session id
        try:
            pid = os.fork()  # fork again to complete the transfer
        except OSError as e:
            raise Exception("{} [{}]".format(e.strerror, e.errno))

        if pid == 0:
            os.chdir(LOGDIR)  # change the working directory to where the logfile will be
            os.umask(UMASK)

        else:  # if we are not the child, exit
            os._exit(0)
    else:
        print('Daemonization complete. You can view the pid number in /tmp/file-syncd.log.'
              ' Use \" kill PID# \" to kill the daemon')
        os._exit(0)

    # Ensures that we cannot have an absurd number of file descriptors
    maxfd = resource.getrlimit(resource.RLIMIT_NOFILE)[1]
    if maxfd == resource.RLIM_INFINITY:
        maxfd = MAXFD

    # Iterate through and close all file descriptors.
    for fd in range(0, maxfd):
        try:
            os.close(fd)
        except OSError:  # ERROR, fd wasn't open to begin with (ignored)
            pass

    os.open(REDIRECT_TO, os.O_RDWR)
    os.dup2(0, 1)  # redirect standard input to stdout
    os.dup2(0, 2)  # redirect stdin to stderr
    return 0


def write_d_info(ret_code):
    procParams = """
           return code = %s
           process ID = %s
           parent process ID = %s
           process group ID = %s
           session ID = %s
           user ID = %s
           effective user ID = %s
           real group ID = %s
           effective group ID = %s
           """ % (ret_code, os.getpid(), os.getppid(), os.getpgrp(), os.getsid(0),
                  os.getuid(), os.geteuid(), os.getgid(), os.getegid())


    dfile = open("file-syncd.log", "w")
    dfile.write(procParams + "\n")
    dfile.flush()
    dfile.close()


class WatchAndSync(FileSystemEventHandler):
    def __init__(self, local_file, remote_file):
        self.local_file = os.path.abspath(local_file)
        self.remote_file = remote_file
        self.observer = Observer(timeout=.1)
        if os.path.isdir(self.local_file):
            print("is directory")
            self.observer.schedule(self, os.path.abspath(local_file), recursive=True)
        else:
            self.observer.schedule(self, os.path.abspath(os.path.dirname(local_file)))

    def sync(self):
        if args.verbose:
            print("Initiating Upload")

        subprocess.run(['rsync', self.local_file, self.remote_file])

        if args.verbose:
            print("Upload Complete")

    def on_change(self, path):
        #print('path is: ' + str(path) + '\n')
        #if path == self.local_file:
        self.sync()

    def on_create(self, event):
        #print("in on create")
        if self.observer.__class__.__name__ == 'InotifyObserver':
            return

        else:
            self.on_change(event.src_path)

    def on_modified(self, event):
        #print('event is', event, self.local_file, '\n')
        #if event.src_path == self.local_file:
        print(event.is_directory)
        self.on_change(event.src_path)

    def on_moved(self, event):
        #print('in on moved, event is', event)
        if event.src_path == self.local_file:
            try:
                self.observer.stop()
                self.observer.join()
            except RuntimeError:
                print("stopped")

            exit(1)

    def run(self):
        self.observer.start()
        if args.verbose:
            print("started")
        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            print('stopped')
            self.observer.stop()
        self.observer.join()


def main():
    if args.daemonize:
        print('daemonizing')
        ret_code = daemonize()
        write_d_info(ret_code)

    was = WatchAndSync(args.local_file, args.remote_file)
    try:
        was.run()
    except KeyboardInterrupt:
        exit(0)

if __name__ == '__main__':
    main()
