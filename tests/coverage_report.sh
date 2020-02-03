#!/bin/bash

/usr/local/bin/coverage run -m unittest discover -s tests/
/usr/bin/python -m unittest discover -s tests/
/usr/local/bin/coverage run -m unittest discover -s tests/
/usr/local/bin/coverage report -m
/usr/local/bin/coverage html
