Diff Coverage Tool
==================

This tool combines the data collected by coverage.py_ with a diff to determine
what if any lines modified or added in the diff are not covered in a coverage
run (generally the running of the test suite).

Currently the implementation assumes this is for a Django patch for
convenience, as that is what I needed at the time - but modifying should be
pretty easy.

Quickstart
----------
First run the Django test suite with coverage:

.. code-block:: console

    coverage run runtests.py --settings=test_sqlite

Assuming you are using git for development generate a diff that you want to use
for comparison:

.. code-block:: console

    git diff master > /path/to/my_patch.diff

then from inside this tool's directory, you need to have your patched version of
django on your python path, for example if you use a django-dev virtualenv:

.. code-block:: console

    python diff_coverage.py /path/to/my_patch.diff

The script will write to stdout files with patched, untested lines and generate
an html report with those files and the lines highlighted (with a red line
number) in the current working directory.



.. _coverage.py: http://pypi.python.org/pypi/coverage
