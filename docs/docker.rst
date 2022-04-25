######
Docker
######

************
Installation
************

The following is a quick cookbook to get ``docker`` and ``docker-compose`` installed on OS X and running a local Solr container.

.. highlight:: sh

::

   $ brew cask install virtualbox
   $ brew install docker docker-compose docker-machine
   $ brew services start docker-machine
   $ docker-machine create planning
   $ eval $(docker-machine env planning)
   $ # now run the "hello-world" image to see if it worked
   $ docker run hello-world

