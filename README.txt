========
Overview
========

check_brocade is a Sensu (and partially with compatible Nagios) check
plugin that can be used to monitor Brocade VDX 6740 and probably related
devices through their REST API.

Operations
==========

You call check_brocade with one of the machines' addresses for their
management interface:

   $ bin/check_brocade switch.my.domain

XXX how to do auth missing


Features
========

* Provides a readable overview of the whole VDX cluster.
* Provides a summary "good"/"bad" decision based on the output from
  the switches various internal checks.
* Includes recent log information as well as the last important log messages.
* Can partially adapt to some of the items that may be variable and get
  reported dynamically by the switches (i.e. hardware components in the
  system section).


Authors
=======

* Christian Theune <ct@flyingcircus.io>


License
=======

GPLv3


Links
=====

* `Brocade VDX 6740 <https://www.brocade.com/en/products-services/switches/data-center-switches/vdx-6740-switches.html>`_

.. vim: set ft=rst spell spelllang=en sw=3:
