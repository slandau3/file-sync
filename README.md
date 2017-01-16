File Sync
==========
File sync is a python script used to synchronize two files between computers. The script can also be used to synchronize directories but that is NOT recommended (the script is not set up for that). If you wish to sync or backup directories to a remote server please use my other project [directory sync](https://github.com/slandau3/Directory-Sync). 

By default the program will sync the given file to the remote machine. Nothing will be downloaded by default.

I specifically created this program so that I can edit files on my machine and have them automatically upload to a remote machine for testing. I initially used an sftp plugin for sublime text to accomplish this goal but I struggled to find a solution for other text editors (such as pycharm or intellij). 


http://www.howtogeek.com/168147/add-public-ssh-key-to-remote-server-in-a-single-command/