# 2.0.8
 Re-published after 2.0.7.170-cp3xx wheels were found to require a newer
 libstdc++ than the manylinux_2_28 policy allows (gcc-toolset-14 was used to
 compile the static hunspell library). Bumped since package feeds don't allow
 re-uploading a version that's already published.

# 2.0.7
 Re-published after 2.0.6.170-cp3xx wheels were found to require glibc >= 2.38
 (built outside the manylinux container by mistake). Bumped since package feeds
 don't allow re-uploading a version that's already published.

# 2.0.6-l1.7.0'
 Revert to use bundled hunspell 1.7.0 because of degraded correction performance with 1.7.3

# 2.0.6
 Support of multilinux built

# 2.0.5
- Updated bundled hunspell from 1.7.0 to 1.7.3

# 2.0.4
- Rebuilt with python 3.12. 
- Update to Cython>=3.2.4

# 2.0.3
- Rebuilt with python 3.10 tested

# 2.0.2
- Removed support for python3.5
- Added support for python3.9

# 2.0.1
- Fixed builds for OSX

# 2.0.0
- Removed support for python 2
- Updated to hunspell 1.7.0
- Added support for `suffix_suggest`
- Added support for `analyze`
- Added support for `add_dic`
- Added support for `remove`
- Added support for `add_with_affix`
- Updated builds to be wheel based
- Moved dictionaries inside hunspell directory structure

# 1.3.3
- Mapped the `add` function to the cython wrapper class.

# 1.3.1 -> 1.3.2
- Fixed dictionary loader to respect locales
- Enabled long file paths to be loaded on windows
- Fixed caching bug which caches results across hunspell instances with different dictionaries.

# 1.3.0
- Fixed build for python 3.7
- Fixed library search issues (> Ubunutu 17)
- Upgraded default hunspell to 1.6.2 for Linux distros

# 1.2.1
- Fixed empty string crash

# 1.2.0
- Fixed detect CPU issue on Linux distros
- Fixed bytes versus unicode conversion for inputs in python2
- Added fix for Python 2.7 on osx
- Added fix for Windows 10 builds

# 1.1.4
- Added Python 3 support

# 1.1.3
- Removed library depdency on cython
- Dropped support for Python 2.6
- Added ability to set concurrency on bulk operations
