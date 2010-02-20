#!/bin/bash

export AWS_KEY=$1
export AWS_SECRET=$2

django-admin.py test --settings=mediasync.tests.settings --pythonpath=../..