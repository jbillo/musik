#Music

A web-based streaming media library and player.

##Getting Started

Prerequisites:
- [Pip](http://www.pip-installer.org/en/latest/)
- [Virtualenv](http://pypi.python.org/pypi/virtualenv)
- [Virtualenvwrapper](http://www.doughellmann.com/projects/virtualenvwrapper/) (optional)
- A fork of this repo

Clone the repo

``` bash
git clone git@github.com:[username]/musik.git
cd musik
```

Set up a virtual environment using virtualenv (or virtualenvwrapper)

``` bash
#virtualenv
virtualenv musik-venv --distribute

#virtualenvwrapper
mkvirtualenv music-venv
```

Activate the virtual environment

``` bash
#virtualenv
source music-venv/bin/activate

#virtualenvwrapper
workon music-venv
```

Install dependencies with pip

``` bash
pip install -r requirements.txt
```

Run the musik server
``` bash
python musik.py
```
The Musik server starts up by default on port 8080
point your browser at [http://localhost:8080/](http://localhost:8080/)

Optionally you can set a PORT environment variable

``` bash
export PORT=5000
python musik.py
```

##Using Foreman (Optional)

Foreman is a command-line tool for running Procfile-backed apps. It allows you to run your app easily with environment variables that do not affect the rest of your system.

Install Foreman, it comes pre-packaged with the [Heroku Toolbelt](https://toolbelt.heroku.com/).

Create a ```.env``` file in your project directory

``` bash
cd musik
touch .env
```

Add any environment variables you wish to your ```.env``` file, here is an example file.

```
PORT=5555
SOME_VAR=blah-blah-blah
```

Start up the Musik server using foreman

``` bash
foreman start
```

Stop the Musik server when running in foreman by hitting ```ctrl-c```

##Contributing

1. Fork this repo
1. Take a look at the issues. What needs to be done?
1. Make a topic branch for what you want to do. Bonus points for referencing an issue (like 2-authentication).
1. Make your changes.
1. Create a Pull Request.
1. Profit!
