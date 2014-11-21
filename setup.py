# -*- coding: utf-8 -*-

"""
---------------------------------------------------------------------------------
"THE BEER-WARE LICENSE" (Revision 42):
<adam.bambuch2@gmail.com> wrote this file. As long as you retain this notice you
can do whatever you want with this stuff. If we meet some day, and you think
this stuff is worth it, you can buy me a beer in return Adam Bambuch
---------------------------------------------------------------------------------
"""

from distutils.core import setup
setup(
    name = "tclib",
    packages = ["tclib", "tclib.world", "tclib.shared", "tclib.shared.modules", "tclib.realm"],
    version = "1.1.0",
    description = "Trinity Core Client Library",
    author = "Adam Bambuch",
    author_email = "adam.bambuch2@gmail.com",
)