Introduction
============

Provides external methods to sync and create content from Adlib API

Features
============
- Creates Object content type in a Plone site based on Adlib API data.
- Synchronization of content from Adlib API with a Plone site.

Installation
===================
If you are using zc.buildout and the plone.recipe.zope2instance recipe to manage your project, you can do this:
Add collective.adlibsyncmanager to the list of eggs to install, e.g.::

	[buildout]
		…
		eggs =
			…
			collective.adlibsyncmanager

How to use method as a cron job?
=======================================================
Add to your buildout.cfg::

	zope-conf-additional = 
	<clock-server> 
		method /SiteName/adlib_sync 
		period 60 
		user username-to-invoke-method-with
		password password-for-user 
		host localhost 
	</clock-server>

Dependencies
===============
- collective.object

The following dependencies are not required unless the creation of pictures and translations is requested.
- plone.namedfile
- plone.app.multilingual 

Todos
==========
- Get deleted records from API and update content
- Create log document with every request result details
- Send email after several failed API request attempts
