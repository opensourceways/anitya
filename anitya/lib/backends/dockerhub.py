import logging
import json
import six
import re
import subprocess

from anitya.lib.backends import REGEX, BaseBackend, get_versions_by_regex
from anitya.lib.exceptions import AnityaPluginException

REGEX_ALIASES = {"DEFAULT": REGEX}

_log = logging.getLogger(__name__)

class DockerhubBackend(BaseBackend):
    """The docker class for project having a special hosting.

    This backend allows to specify a version_url and a regex that will
    be used to retrieve the version information.
    """

    name = "Dockerhub"
    examples = [
        "https://hub.docker.com/r/openeuler/redis/tags"
    ]
    more_info = (
        "More information in the <a href='"
        "/static/docs/user-guide.html#regular-expressions'> "
        "user-guide.html#regular-expressions</a>"
    )
    default_regex = REGEX % {"name": "{project name}"}
    default_version_scheme = "ModifiedSemantic"

    @classmethod
    def get_version_url(cls, project):
        """Method called to retrieve the url used to check for new version
        of the project provided, project that relies on the backend of this plugin.

        Attributes:
            project (:obj:`anitya.db.models.Project`): Project object whose backend
                corresponds to the current plugin.

        Returns:
            str: url used for version checking
        """
        url = f"https://hub.docker.com/v2/repositories/{project.version_url}/tags/?page_size=100&page=1&name&ordering"

        return url

    @classmethod
    def get_versions(cls, project):
        """Method called to retrieve all the versions (that can be found)
        of the projects provided, project that relies on the backend of
        this plugin.

        :arg Project project: a :class:`anitya.db.models.Project` object whose backend
            corresponds to the current plugin.
        :return: a list of all the possible releases found
        :return type: list
        :raise AnityaPluginException: a
            :class:`anitya.lib.exceptions.AnityaPluginException` exception
            when the versions cannot be retrieved correctly

        """
        url = cls.get_version_url(project)

        upstream_versions = []
        while url: 
            try:
                req = BaseBackend.call_url(url, last_change=project.get_time_last_created_version(), insecure=project.insecure)
            except Exception as err:
                _log.debug("%s ERROR: %s", project.name, str(err))
                raise AnityaPluginException(
                    f'Could not call : "{url}" of "{project.name}", with error: {str(err)}'
                ) from err

            if not isinstance(req, six.string_types):
                # Not modified
                if req.status_code == 304:
                    return []
                req = req.text

            try:
                response = json.loads(req)
                url = response.get("next")
                for _, result in enumerate(response.get("results")):
                    upstream_versions.append(result.get("name"))
            except Exception as err:
                _log.debug("%s ERROR: %s", project.name, str(err))
                raise AnityaPluginException(
                    f"{project.name}: parse response json fail"
                ) from err

        upstream_versions = list(set(upstream_versions))
        upstream_versions = [v for v in upstream_versions if bool(re.search(r'\d', v))]

        if len(upstream_versions) == 0:
            raise AnityaPluginException(
                f"{project.name}: no upstream version found"
            )
        # Filter retrieved versions
        filtered_versions = BaseBackend.filter_versions(
            upstream_versions, project.version_filter
        )
        return filtered_versions

    @classmethod
    def check_feed(cls):  # pragma: no cover
        """Method called to retrieve the latest uploads to a given backend,
        via, for example, RSS or an API.

        Not Supported

        Returns:
            :obj:`list`: A list of 4-tuples, containing the project name, homepage, the
            backend, and the version.

        Raises:
             NotImplementedError: If backend does not
                support batch updates.

        """
        raise NotImplementedError()

    @classmethod
    def get_architecture_url(cls, project):
        url = f"docker manifest inspect {project.architecture_url}"

        return url

    @classmethod
    def get_architectures(cls, project):
        url = cls.get_architecture_url(project)

        support_architectures = []
        try:
            res = subprocess.Popen(url, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            for line in res.stdout.readlines():
                line = line.decode("utf-8")
                if "\"architecture\":" in line:
                    support_architectures.append(
                        line.replace("\"architecture\":", "").replace("\"", "").replace(",", "").strip()
                    )
        except Exception as err:
            _log.debug("%s ERROR: %s", project.name, str(err))
            raise AnityaPluginException(
                f"{project.name}: get architectures fail"
            ) from err

        support_architectures = list(set(support_architectures))
        if "unknown" in support_architectures:
            support_architectures.remove("unknown")

        return ",".join(str(v) for v in sorted(support_architectures))
