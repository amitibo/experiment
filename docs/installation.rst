.. highlight:: shell

============
Installation
============


Stable release
--------------

To install Experiment, run this command in your terminal:

.. code-block:: console

    $ pip install experiment

This is the preferred method to install Experiment, as it will always install the most recent stable release.

If you don't have `pip`_ installed, this `Python installation guide`_ can guide
you through the process.

.. _pip: https://pip.pypa.io
.. _Python installation guide: http://docs.python-guide.org/en/latest/starting/installation/


From sources
------------

The sources for Experiment can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git://github.com/amitibo/experiment

Or download the `tarball`_:

.. code-block:: console

    $ curl  -OL https://github.ibm.com/AMITAID/experiment/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install

To compile the documentation (should be executed from within a node with cuda drivers):

.. code-block:: console

    cd docs
    make rst
    make html
    make pdf

To view the documentation using a browser:

.. code-block:: console

    cd ../../
    sphinx-serve -p 8080 -b experiment-docs

Direct a browser to the *ip* of the ccc node (get be retrived by *ifconfig* command)
and the port set by the *sphinx-serve* command (8080).


.. _Github repo: https://github.ibm.com/AMITAID/experiment
.. _tarball: https://github.ibm.com/AMITAID/experiment/tarball/master
