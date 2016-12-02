Contributing to snsync
#########################

So you want to contribute? That makes you a rock star! :)

Please take 5 minutes to read this and familiarise yourself with these guidelines.

The first rule of GitHub
------------------------

If you've not used github before getting started can be a bit daunting, if you want to propose a feature or fix a bug start by `Forking`_ that will create a local copy of snsync in your github account.
Next `create a branch`_ and make your changes in there. Branching not only fits neatly into the github work flow (*you'll notice a button appear in github that says "create a pull request for this branch"*) but it keeps git tidy under the hood.
Finally `create a pull request`_ (*PR*). The PR will create an issue for me to review and make it easy to include your suggestions.

Errors and Bug Fixes
--------------------

If you have a problem with snsync you can create an issue; please ensure that all issues include the ``Python version`` and any debugs or traces you think would be helpful, possibly the contents of the offending Note or Simplenote.

Where possible, please suggest a fix via a *PR*

New Features
-------------

If you have an idea to improve snsync, that's great!

1. Where possible, please implement new features as a function
2. All new functions will require `a test`_  ( *and shouldn't break* `existing tests`_ )
3. All new functions will require `documentation`_ , i.e. comments that work with sphinx-autodoc.

Please ask if you have any problems with these. 

Documentation
-------------

English is my native language but that doesn't mean I'm perfect at it, inspection and suggestions from the grammar police are welcome.

Thanks for reading!
^^^^^^^^^^^^^^^^^^^

.. Links
.. _`Forking`: https://help.github.com/articles/fork-a-repo/
.. _`create a branch`: https://help.github.com/articles/creating-and-deleting-branches-within-your-repository/
.. _`create a pull request`: https://help.github.com/articles/creating-a-pull-request/
.. _`a test`: https://github.com/linickx/snsync/issues/2
.. _`existing tests`: https://github.com/linickx/snsync/issues/2
.. _`documentation`: https://github.com/linickx/snsync/issues/1
