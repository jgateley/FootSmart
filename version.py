import semver
import grammar as jg

intuitive_version = '1.1.0'


def version_verify(elem, _ctxt, _lp):
    # This should only happen when genning a Morningstar backup file, no version specified
    if elem is None:
        return intuitive_version
    desired_version = semver.Version.parse(intuitive_version)
    have_version = semver.Version.parse(elem)
    if have_version.is_compatible(desired_version):
        return elem
    raise jg.GrammarException('bad_version', "Intuitive config file version is wrong. Currently on " +
                              intuitive_version + " but got " + elem)
