# coding: utf-8

from flask import render_template
from ..models.pub import Pub
from ..models.tools import get_one


def scratch_home():
    return render_template('scratch.html')


def ticket_web():
    pass