"""
Test the _utils.cache_mixin module
"""
import json
import os
import shutil
import tempfile
from pathlib import Path

import pytest

from joblib import Memory

import nilearn
from nilearn._utils import cache_mixin, CacheMixin


def _get_subdirs(top_dir):
    top_dir = Path(top_dir)
    children = list(top_dir.glob("*"))
    return [child for child in children if child.is_dir()]


def f(x):
    # A simple test function
    return x


def test_check_memory():
    # Test if _check_memory returns a memory object with the location equal to
    # input path
    with tempfile.TemporaryDirectory() as temp_dir:

        mem_none = Memory(location=None)
        mem_temp = Memory(location=temp_dir)

        for mem in [None, mem_none]:
            memory = cache_mixin._check_memory(mem, verbose=False)
            assert memory, Memory
            assert memory.location == mem_none.location

        for mem in [temp_dir, mem_temp]:
            memory = cache_mixin._check_memory(mem, verbose=False)
            assert memory.location == mem_temp.location
            assert memory, Memory


def test_cache_memory_level():
    with tempfile.TemporaryDirectory() as temp_dir:
        joblib_dir = Path(
            temp_dir, 'joblib', 'nilearn', 'tests', 'test_cache_mixin', 'f')
        mem = Memory(location=temp_dir, verbose=0)
        cache_mixin.cache(f, mem, func_memory_level=2, memory_level=1)(2)
        assert len(_get_subdirs(joblib_dir)) == 0
        cache_mixin.cache(f, Memory(location=None))(2)
        assert len(_get_subdirs(joblib_dir)) == 0
        cache_mixin.cache(f, mem, func_memory_level=2, memory_level=3)(2)
        assert len(_get_subdirs(joblib_dir)) == 1
        cache_mixin.cache(f, mem)(3)
        assert len(_get_subdirs(joblib_dir)) == 2


class CacheMixinTest(CacheMixin):
    """Dummy mock object that wraps a CacheMixin."""

    def __init__(self, memory=None, memory_level=1):
        self.memory = memory
        self.memory_level = memory_level

    def run(self):
        self._cache(f)


def test_cache_mixin_with_expand_user():
    # Test the memory cache is correctly created when using ~.
    cache_dir = "~/nilearn_data/test_cache"
    expand_cache_dir = os.path.expanduser(cache_dir)
    mixin_mock = CacheMixinTest(cache_dir)

    try:
        assert not os.path.exists(expand_cache_dir)
        mixin_mock.run()
        assert os.path.exists(expand_cache_dir)
    finally:
        if os.path.exists(expand_cache_dir):
            shutil.rmtree(expand_cache_dir)


def test_cache_mixin_without_expand_user():
    # Test the memory cache is correctly created when using ~.
    cache_dir = "~/nilearn_data/test_cache"
    expand_cache_dir = os.path.expanduser(cache_dir)
    mixin_mock = CacheMixinTest(cache_dir)

    try:
        assert not os.path.exists(expand_cache_dir)
        nilearn.EXPAND_PATH_WILDCARDS = False
        with pytest.raises(
                ValueError,
                match="Given cache path parent directory doesn't"):
            mixin_mock.run()
        assert not os.path.exists(expand_cache_dir)
        nilearn.EXPAND_PATH_WILDCARDS = True
    finally:
        if os.path.exists(expand_cache_dir):
            shutil.rmtree(expand_cache_dir)


def test_cache_mixin_wrong_dirs():
    # Test the memory cache raises a ValueError when input base path doesn't
    # exist.

    for cache_dir in ("/bad_dir/cache",
                      "~/nilearn_data/tmp/test_cache"):
        expand_cache_dir = os.path.expanduser(cache_dir)
        mixin_mock = CacheMixinTest(cache_dir)

        try:
            with pytest.raises(
                    ValueError,
                    match="Given cache path parent directory doesn't"):
                mixin_mock.run()
            assert not os.path.exists(expand_cache_dir)
        finally:
            if os.path.exists(expand_cache_dir):
                shutil.rmtree(expand_cache_dir)


def test_cache_shelving():
    with tempfile.TemporaryDirectory() as temp_dir:
        joblib_dir = Path(
            temp_dir, 'joblib', 'nilearn', 'tests', 'test_cache_mixin', 'f')
        mem = Memory(location=temp_dir, verbose=0)
        res = cache_mixin.cache(f, mem, shelve=True)(2)
        assert res.get() == 2
        assert len(_get_subdirs(joblib_dir)) == 1
        res = cache_mixin.cache(f, mem, shelve=True)(2)
        assert res.get() == 2
        assert len(_get_subdirs(joblib_dir)) == 1
