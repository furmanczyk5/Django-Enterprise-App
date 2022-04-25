.. Planning.org Documentation documentation master file, created by
   sphinx-quickstart on Mon May  7 08:37:17 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

##########################
Planning.org Documentation
##########################


This is the main documentation for various software development and IT processes and configuration for the planning.org web platform.

Autodocs can be built with `sphinx-apidoc <http://www.sphinx-doc.org/en/master/man/sphinx-apidoc.html>`_.

.. note::

   The EXCLUDE pattern of sphinx-apidoc is really finicky. To get it to exclude migrations, for example, the only thing that's worked for me so far is path relative to the module name, as in:

   sphinx-apidoc -o docs/module_reference/cm cm cm/migrations cm/tests

.. toctree::
   :maxdepth: 2
   :caption: Contents:

   local_dev_setup
   server_config
   integration_wcw
   integration_cadmium_app
   solr
   celerybeat
   icomoon
   imis
   postgres
   integration_cadmium
   myorg

******************
Indices and tables
******************

* :ref:`genindex`
.. * :ref:`modindex`
* :ref:`search`
