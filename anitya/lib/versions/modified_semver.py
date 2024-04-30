# -*- coding: utf-8 -*-
#
# Copyright © 2019  Red Hat, Inc.
#
# This copyrighted material is made available to anyone wishing to use,
# modify, copy, or redistribute it subject to the terms and conditions
# of the GNU General Public License v.2, or (at your option) any later
# version.  This program is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY expressed or implied, including the
# implied warranties of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE.  See the GNU General Public License for more details.  You
# should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# Any Red Hat trademarks that are incorporated in the source
# code or documentation are not subject to the GNU General Public
# License and may only be used or replicated with the express permission
# of Red Hat, Inc.
"""
This adds support for comparing project versions using the semantic version rules.

See `Semantic versioning`_.

.. _Semantic versioning:
   https://semver.org/
"""
import functools

import semver
import re

from .base import Version
from typing import Optional
from datetime import datetime

from anitya.lib.exceptions import InvalidVersion

@functools.total_ordering
class ModifiedSemanticVersion(Version):
    """
    This implements an semantic version plugin.

    It sorts versions using the semantic Python library.
    """

    name = "ModifiedSemantic"

    def __init__(
        self,
        version: Optional[str] = None,
        prefix: Optional[str] = None,
        created_on: Optional[datetime] = None,
        pattern: Optional[str] = None,
        cursor: Optional[str] = None,
        commit_url: Optional[str] = None,
        pre_release_filter: Optional[str] = None,
        oe_version: Optional[str] = None,
    ):
        """
        Constructor of Version class.

        Params:
            version: Raw version
            prefix: Prefix to remove
            created_on: Date of creation
            pattern: Calendar version pattern.
                See `Calendar version scheme_` for more information.
            cursor: An opaque, backend-specific cursor pointing to the version.
            commit_url: A URL pointing to the commit tagged as the version.
            pre_release_filter: A filter used to identify pre-release versions
        """
        super().__init__(
            version, prefix, created_on, pattern, cursor, commit_url, pre_release_filter, oe_version
        )

        if self.oe_version:
            return

        versions = version.split("-", 1)

        if len(versions) == 2:
            self.version = versions[0]
            self.oe_version = versions[1] if bool(re.search(r'\d', versions[1])) else None

    def prerelease(self) -> bool:
        """
        Check if a version is a pre-release version.

        This recognizes versions containing pre-release string according to semantic
        versioning standard. See `Semantic versioning`_.

        Returns:
            (bool) pre-release flag.

        .. _Semantic versioning:
           https://semver.org/
        """
        try:
            version_info = semver.VersionInfo.parse(self.parse())
        except ValueError:
            # version is not correct semantic version, so it's not a pre-release
            return False

        if version_info.prerelease:
            return True

        return super().prerelease()

    def __eq__(self, other):
        """
        Compare two versions for equality using the semantic rules with pre-release
        support.

        Params:
            other (`SemanticVersion`): Version object to compare to

        Returns:
            (bool) Comparision result.
        """
        try:
            result = semver.compare(self.parse(), other.parse())
        except ValueError:
            # version is not correct semantic version, compare as strings
            if self.parse() != other.parse():
                return False
            else:
                return True

        if result != 0:
            return False

        return True

    def __lt__(self, other):
        """
        Compare two versions for lower than using the semantic rules with pre-release
        support.

        Params:
            other (`SemanticVersion`): Version object to compare to

        Returns:
            (bool) Comparision result.
        """
        try:
            result = semver.compare(self.parse(), other.parse())
        except ValueError:
            # Try to parse first version, to be sure which one caused the error
            try:
                semver.VersionInfo.parse(self.parse())
            except ValueError:
                # version is not correct semantic version always assume true
                # This will move the non semantic versions to bottom
                return True
            return False

        if result != -1:
            return False

        return True
