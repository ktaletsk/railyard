========
Railyard
========


.. image:: https://img.shields.io/pypi/v/railyard.svg
        :target: https://pypi.python.org/pypi/railyard

.. image:: https://img.shields.io/travis/ktaletsk/railyard.svg
        :target: https://travis-ci.com/ktaletsk/railyard

.. image:: https://readthedocs.org/projects/railyard/badge/?version=latest
        :target: https://railyard.readthedocs.io/en/latest/?badge=latest
        :alt: Documentation Status




Modular Jupyter Ncontainer builds from Yaml definitions


* Free software: MIT license
* Documentation: https://railyard.readthedocs.io.


Features
--------

* Container image template using popular package managers and best practices
* Stack (additional languages/kernels/dependencies) defined in .yaml file
* Build and push images for all combinations of stacks
* (Coming next) Jenkins pipeline for CI/CD integration
* (Coming next) Tracking of package updates and bot creating PRs
* (Coming next) Automatic tests of containers

Interactive demo
----------------

Try configuring your container at the link below. Pick and choose languages and packages you need, get the container ID and use it whenever you want: pull and use on your local machine / config to use on JupyterHub instances. All images are already prebuilt and kept up to date.

[![Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/ktaletsk/railyard/master?urlpath=%2Fvoila%2Frender%2Fbuilder-ui%2FContainerBuilder.ipynb)

Credits
-------

This package was created with Cookiecutter_ and the `audreyr/cookiecutter-pypackage`_ project template.

.. _Cookiecutter: https://github.com/audreyr/cookiecutter
.. _`audreyr/cookiecutter-pypackage`: https://github.com/audreyr/cookiecutter-pypackage