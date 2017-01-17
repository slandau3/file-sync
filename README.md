File Sync
==========
File sync is a python script used to synchronize one file between computers. The script can also be used to synchronize directories but that is NOT recommended (the script is not set up for that). If you wish to sync or backup directories to a remote server please use my other project [directory sync](https://github.com/slandau3/Directory-Sync). 

By default the program will sync the given file to the remote machine. Every time the file is modified it will be re-uploaded to the remote machine. The process can also be run as a daemon with the -d or --daemon flags. When run as a daemon, a file int /tmp will be created titled "file-syncd.log" Information such as the pid is located in the file.

I specifically created this program so that I can edit files on my machine and have them automatically upload to a remote machine for testing. I initially used an sftp plugin for sublime text to accomplish this goal but I struggled to find a solution for other text editors (such as pycharm or intellij). 

The program requires that you have your ssh key in the remote machines authorized keys. The program will not work if a password is required. See this link for information on how to generate an ssh key and add it to the list of authorized keys:cd 
http://www.howtogeek.com/168147/add-public-ssh-key-to-remote-server-in-a-single-command/

~Usage
    
    python3 file-sync.py [OPTIONS] local_file remote_file
    
 ~
 example:
 
 python3 file-sync.py foo.txt person@192.168.1.1:/home/person/foo.txt