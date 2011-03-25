import simplesync.main

from distutils.core import setup

setup(name = "simplesync",
    version = simplesync.main.get_version(),
    description = "simple syncronization tool",
    author = "Jochen Skulj",
    author_email = "jochen@jochenskulj.de",
    url = "http://www.jochenskulj.de",
    packages = ["simplesync"],
    scripts = ["ssync"],
    long_description = """simple syncronization tool""" 
) 
