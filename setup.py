# dpp2xmp <http://github.com/jmullan/dpp2xmp>
# Copyright 2014 Jesse Muillan

# This file is part of dpp2xmp.
#
# dpp2xmp is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# dpp2xmp is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with dpp2xmp.  If not, see <http://www.gnu.org/licenses/>.

from distutils.core import setup

setup(name="dpp2xmp",
      version="0.0.1",
      description="Extract stuff from Digital Photo Professional into XMP",
      license="GPLv3+",
      author="Jesse Mullan",
      author_email="jmullan@visi.com",
      url="",
      classifiers=[
          "Development Status :: 3 - Alpha",
          "Intended Audience :: Developers",
          "License :: OSI Approved :: GNU General Public License v3 or later (GPLv3+)",
          "Programming Language :: Python :: 2.6",
          "Programming Language :: Python :: 2.7",
          "Programming Language :: Python :: 3",
          "Topic :: Multimedia"],
      py_modules=["dpp2xmp"])
