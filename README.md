Glassistant: Cognitive Assistant based on Google Glass
========================================================
Glassistant is a framework to write cognitive assistants that utilizes computer vision and runs on Google Glass. It is built on []Gabriel infrastructure](https://github.com/cmusatyalab/gabriel).

* `android` directory contains the started code for the Android client.
* `bin` contains the binaries to run the framework on the cloud.
* `assistant` contains the code for the cognitive assistant.

For questions and feedback, please email icanberk@andrew.cmu.edu

Copyright (C) 2013-2014 Carnegie Mellon University
This is a developing project and some features might not be stable yet.


License
----------
All source code, documentation, and related artifacts associated with the
Glassistant project are licensed under the [Apache License, Version
2.0](http://www.apache.org/licenses/LICENSE-2.0.html).

A copy of this license is reproduced in the [LICENSE](LICENSE) file.


Installation - Glassistant
-------------

Ensure the `python` executable on your PATH is Python 2
with `python --version`.
If you are using Python 3, setup and use a
[virtualenv][virtualenv] in an external directory
so that the `python` on your PATH is Python 2.

+ Initialize the virtual environment with `virtualenv -p python2.7 ~/.env-2.7`.
+ Use the environment with `source ~/.env-2.7/bin/activate`.
+ Stop using the environment with `deactivate`.

Replacing the symlink in a directory such as `/usr/bin/python`
is __not__ recommended because this can potentially break
other Python 3 applications.

You will also need the following packages.

* parallel-ssh
* psutil >= 0.4.1
* JRE for UPnP
* six==1.1.0
* Flask==0.9
* Flask-RESTful==0.2.1


To install, you can either

* run a installation script::

    > $ sudo apt-get install fabric openssh-server
    > $ fab localhost install

* install manually::

    > sudo apt-get install default-jre python-pip pssh python-psutil
    > sudo pip install flask==0.9 flask-restful==0.2.1 six==1.1.0


Installation - Default networking interface.
-------------
If your default networking interface is not `eth0`,
the current method to configuring other interfaces is
to replace `eth0` occurrences in the following files.

+ `<gabriel-repo>/gabriel/lib/gabriel_REST_server`
+ `<gabriel-repo>/bin/gabriel-ucomm`


Installation - Application
-------------

Described at README file of each application directory



Tested platforms
---------------------

We have tested at __Ubuntu 12.04 LTS 64-bit__ but it should work well other
version of Ubuntu with a current installation script. We expect this code also
works other Linux distributions as long as you can install required package.



How to use
--------------

1. Run the `control server` from the binary directory.

    ```
    $ cd <gabriel-repo>/bin
    $ ./gabriel-control
    INFO     Start RESTful API Server
    INFO     Start UPnP Server
    INFO     Start monitoring offload engines
    INFO     * Mobile server(<class 'mobile_server.MobileVideoHandler'>) configuration
    INFO      - Open TCP Server at ('0.0.0.0', 9098)
    INFO      - Disable nagle (No TCP delay)  : 1
    INFO     --------------------------------------------------
    INFO     * Mobile server(<class 'mobile_server.MobileAccHandler'>) configuration
    INFO      - Open TCP Server at ('0.0.0.0', 9099)
    INFO      - Disable nagle (No TCP delay)  : 1
    INFO     --------------------------------------------------
    INFO     * Mobile server(<class 'mobile_server.MobileResultHandler'>) configuration
    INFO      - Open TCP Server at ('0.0.0.0', 9101)
    INFO      - Disable nagle (No TCP delay)  : 1
    INFO     --------------------------------------------------
    INFO     * Application server(<class 'app_server.VideoSensorHandler'>) configuration
    INFO      - Open TCP Server at ('0.0.0.0', 10101)
    INFO      - Disable nagle (No TCP delay)  : 1
    INFO     --------------------------------------------------
    INFO     * Application server(<class 'app_server.AccSensorHandler'>) configuration
    INFO      - Open TCP Server at ('0.0.0.0', 10102)
    INFO      - Disable nagle (No TCP delay)  : 1
    INFO     --------------------------------------------------
    INFO     * UComm server configuration
    INFO      - Open TCP Server at ('0.0.0.0', 9090)
    INFO      - Disable nagle (No TCP delay)  : 1
    INFO     --------------------------------------------------
    ```

2. Run `ucomm server` from the binary directory.

    ```
    $ cd <gabriel-repo>/bin
    $ ./gabriel-ucomm
    INFO     execute : java -jar /home/krha/gabriel/src/control/lib/gabriel_upnp_client.jar
      ...
    INFO    Gabriel Server :
      ...
    INFO    connecting to x.x.x.x:9090
    INFO    * UCOMM server configuration
    INFO     - Open TCP Server at ('0.0.0.0', 10120)
    INFO     - Disable nagle (No TCP delay)  : 1
    INFO    --------------------------------------------------
    INFO    Start forwarding data
    ```

    If `ucomm server` is successfully connected to `control server`, you can see
    a log message __"INFO     User communication module is connected"__ at
    `control server`.

3. Run the cognitive engine.

   
   python gabriel-app-starter.py will run your code at `assistant` app

4. Run a mobile client using source code at `<gabriel-repo>/android/`. Make sure to
   change IP address of `GABRIEL_IP` variable at
   `src/edu/cmu/cs/gabriel/Const.java`.


