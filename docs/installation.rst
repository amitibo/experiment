.. highlight:: shell

============
Installation
============


From sources
------------

The sources for Experiment can be downloaded from the `Github repo`_.

You can either clone the public repository:

.. code-block:: console

    $ git clone git@github.com:amitibo/experiment.git

Or download the `tarball`_:

.. code-block:: console

    $ curl  -OL https://github.com/amitibo/experiment/tarball/master

Once you have a copy of the source, you can install it with:

.. code-block:: console

    $ python setup.py install

To compile the documentation (should be executed from within a node with cuda drivers):

.. code-block:: console

    $ cd docs
    $ make rst
    $ make html

To view the documentation using a browser:

.. code-block:: console

    $ cd ../../
    $ sphinx-serve -p 8080 -b experiment-docs

Direct a browser to the *ip* of the ccc node (get be retrived by *ifconfig* command)
and the port set by the *sphinx-serve* command (8080).


.. _Github repo: https://github.com/amitibo/experiment
.. _tarball: https://github.com/amitibo/experiment/tarball/master
