# -*- coding: utf-8 -*-
"""
THIS FILE IS PART OF CLASPLINT BY MATT BELFAST BROWN
CLASPLint.__init__ -- Package entry point and public API surface.

Exposes the runner and reporter modules as the primary public interface for
programmatic use of the CLASP 3.1.1 / PEP 2606 static analysis engine.

Author: Matt Belfast Brown
Create Date: 2026-06-17
Version Date: 2026-07-01
Version: 0.3.0

THIS PROGRAM IS LICENSED UNDER GPL-3.0
YOU SHOULD HAVE RECEIVED A COPY OF GPL-3.0 LICENSE.

Copyright (C) 2026 Matt Belfast Brown

CLASPLint is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, version 3 of the License.

CLASPLint is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty
of MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with CLASPLint.  If not, see <https://www.gnu.org/licenses/>.
"""

# Define the package version string.
__version__ = "0.3.0"
# Expose the runner and reporter modules as the public API.
__all__ = ["runner", "reporter"]
