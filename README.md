# Grow - Telos Testing Tool

Grow is a Telos development tool that allows quick deployment of genesis nodes, or private testing clusters. Grow affords users more convenient short hand commands for locking and unlock wallets, creating staked accounts on a network, or generating key pairs for later use.

## Resources

1. [Installation](#Installation)
2. Tour (Coming Soon)
3. Starting a Genesis Node (Coming Soon)
4. Starting a Private Mesh (Coming Soon)

### Installation

This section will explain how to clone grow, install its dependencies, and add it to your servers .bachrc or .bash_profile shell script.

1. First we need to clone grow, so go to the directory you'd like to clone grow and run `git clone https://github.com/Telos-Foundation/grow -b stage2.0`
2. Next we need to have python 3.5 or greater installed. To check run `python3 --version`. If you don't have python3 [here](https://realpython.com/installing-python/) are the installation instructions.
3. Now we check to make sure we have pip3, run `pip3 --version`.
    1. If pip3 gives you a version output move onto step 4, otherwise run the command specific to your OS.
        1. Ubuntu - run `sudo apt install python3-pip`
        2. Darwin (Mac OS X) - run `brew install python3`
4. Now we need to install grows dependencies.
    1. Navigate to the grow tool directory `cd /{path-to-grow}/`
    2. run `pip3 install -r requirements.txt`
    3. This command will install all the packages outlined in requirements.txt
    4. run `./grow.py`, to make sure you are getting the help message.
5. Now we want to add grow to you `$PATH` variable. Please check below for your operating system.
    1. #### Ubuntu
        1. navigate to your home directory, `cd ~/`
        2. edit `.bashrc`, `vim .bashrc`
        3. Add the below lines to your file.
            1. `export PATH=$PATH:/{path-to-grow}/`
            2. `alias grow="grow.py"`
    2. #### Mac OS X
        1. navigate to your home directory, `cd ~/`
        2. edit `.bash_profile`, `vim .bash_profile`
        3. Add the below lines to your file.
            1. `export PATH=$PATH:/{path-to-grow}/`
            2. `alias grow="grow.py"`
6. Grow should be ready to use anywhere on your system. Make a testing folder and try starting a genesis node.
    1. `mkdir tests`
    2. `cd tests`
    3. `grow spin full`