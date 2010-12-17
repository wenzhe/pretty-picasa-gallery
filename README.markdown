Pretty Picasa Gallery
=====================

## About

This is a python photo gallery designed to run on Google's App Engine. Currently, photos are hosted on Picasa and the gallery reads the album list and displays those on a more professional looking gallery page, complete with Lightbox support.

## Features
* Picasa photo backend support
* User configurable album support
* Various photo sizes support
* Random front page photo
* Permalinks to photos

## Running

Download the source code from github and install the Google App Engine SDK.  Once the source is downloaded, go to that location in a terminal and run the dev_appserver.py command.  For instance:


    [streeter@mordecai]:~$ cd pretty-picasa-gallery/
    [streeter@mordecai]:~/pretty-picasa-gallery$ dev_appserver.py .
    INFO     2010-12-17 21:04:32,643 appengine_rpc.py:153] Server: appengine.google.com
    INFO     2010-12-17 21:04:32,927 appcfg.py:414] Checking for updates to the SDK.
    INFO     2010-12-17 21:04:35,173 appcfg.py:428] The SDK is up to date.
    INFO     2010-12-17 21:04:35,435 dev_appserver_main.py:485] Running application chris-gallery on port 8080: http://localhost:8080

Then go to the site `http://localhost:8080/admin/` in your browser.  You should be asked to log into your account. From here, enter in your google account id (or whatever email is associated with your picasa account) and choose to log in as an administrator. For example, log in as `<your gmail id>@gmail.com` This will redirect you to the admin page. On this page, fill in some values:

* Photo provider id should be your gmail id without the `@gmail.com`
* Site title should be whatever you want it to be
* Site header should be whatever you want it to be

Click save which will refresh the page and list your albums. Here, choose your homepage album and check the boxes for the albums you want to be displayed, and, optionally, if you want an album that displays all the featured albums together on one page.

Optionally fill in the last two boxes with your Google Analytics ID and your Google Checkout Merchant ID.

## Installation

To run this, you'll want to deploy to App Engine. To do this, edit the file `app.yaml` and change the `application` and `version` parameters. `application` should be set to whatever your application is named, in other words, if your app's url is `your-app-name.appspot.com`, then use `your-app-name`. `version` is used for rollbacks. So it should be set to 1 if this is your first time deploying.

Then, from within the source directory, run

    appcfg.py update .

and enter your login and password. Once the upload finishes, go to your application's url and run through the steps in the **Running** section above.

## Known Issues
* Flickr backend doesn't work
* Installation process could use some work
* When no merchant ID is entered, we still show a price for photos
* Photo price is hard coded
* Picasa albums must be public


Current release is version 1.1