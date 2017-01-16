#!/usr/bin/env python3


import argparse
import sys
import os
import time
import subprocess
import re

parser = argparse.ArgumentParser()
parser.add_argument('-v', '--verbose', action='store_true', help='Print whenever a transfer (upload) '
                                                                 'has been initiated/completed')
parser.add_argument('-d', '--daemonize', action='store_true', help='Instead of running in the local terminal '
                                                                   'make the process into a daemon. This will '
                                                                   'overwrite verbosity')
parser.add_argument('local_file', help="The local file to watch and transfer")
parser.add_argument('remote_file', help="The remote file to be updated to the local_file")
args = parser.parse_args()

LAST_UPLOAD_TIME = 0


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


def sync(local_file, remote_file):
    # Separate file directory from address of remote file
    address = extract_address(remote_file)
    file_loc = extract_file_location(remote_file)

    # Obtain the local modification time of the file we are watching
    try:
        local_mod_time = os.path.getmtime(local_file)
    except FileNotFoundError:
        try: # If the file does not exist on our machine, check to see if it exists on the remote
            subprocess.run(['rsync', remote_file, local_file])
            local_mod_time = os.path.getmtime(local_file)
        except FileNotFoundError:
            raise FileNotFoundError("Neither local file nor remote file exist!")

    # If the file has not changed, don't upload
    global LAST_UPLOAD_TIME
    if LAST_UPLOAD_TIME == local_mod_time:
        return
    else:
        LAST_UPLOAD_TIME = local_mod_time


    remote_dir_list = file_loc.split('/')
    actual_remote_file = remote_dir_list[-1]
    path_to_remote_file = "/".join(remote_dir_list[:-1])

    remote_file_info = subprocess.run(['ssh', address, 'cd {file_loc}; stat -c %Y {remote_file}; exit'
                       .format(file_loc=path_to_remote_file, remote_file=actual_remote_file)],
                       stdout=subprocess.PIPE)
    remote_file_info = remote_file_info.stdout.decode('UTF-8')

    if remote_file_info == '':
        remote_mod_time = 0
    else:
        #remote_mod_time = extract_time(remote_file_info)
        remote_mod_time = float(remote_file_info)

    print('remote: ' + str(remote_mod_time))
    print('local: ' + str(local_mod_time))
    time_diff = local_mod_time - remote_mod_time

    print('time diff is ' + str(time_diff))


    #if time_diff < 0 and not args.local_only:  # Update the local file if the remote is newer
        #subprocess.run(['rsync', remote_file, local_file])
        #print("updating local")
        #return

    if time_diff <= 0:
        return

    # Need to update the remote
    if args.verbose:
        print("uploading file")

    subprocess.run(['rsync', local_file, remote_file])

    if args.verbose:
        print("Finished uploading file")


def extract_address(remote):
    return remote.split(':')[0]


def extract_file_location(remote):
    return remote.split(':')[1]


if __name__ == '__main__':

    local_file = args.local_file
    remote_file = args.remote_file

    if args.daemonize:
        print('daemonizing')
        ret_code = daemonize()
        write_d_info(ret_code)

    while True:
        sync(local_file, remote_file)
        time.sleep(1)

