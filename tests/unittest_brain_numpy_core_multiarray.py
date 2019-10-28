# -*- encoding=utf-8 -*-
# Copyright (c) 2017-2018 hippo91 <guillaume.peillex@gmail.com>

# Licensed under the LGPL: https://www.gnu.org/licenses/old-licenses/lgpl-2.1.en.html
# For details: https://github.com/PyCQA/astroid/blob/master/COPYING.LESSER
import unittest

try:
    import numpy  # pylint: disable=unused-import

    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

from astroid import builder


@unittest.skipUnless(HAS_NUMPY, "This test requires the numpy library.")
class BrainNumpyCoreMultiarrayTest(unittest.TestCase):
    """
    Test the numpy core multiarray brain module
    """

    numpy_functions = (
        ("array", "[1, 2]"),
        ("inner", "[1, 2]", "[1, 2]"),
        ("vdot", "[1, 2]", "[1, 2]"),
        ("concatenate", "([1, 2], [1, 2])"),
        ("dot", "[1, 2]", "[1, 2]"),
        ("empty_like", "[1, 2]"),
        ("where", "[True, False]", "[1, 2]", "[2, 1]"),
        ("empty", "[1, 2]"),
        ("zeros", "[1, 2]"),
    )

    def _inferred_numpy_func_call(self, func_name, *func_args):
        node = builder.extract_node(
            """
        import numpy as np
        func = np.{:s}
        func({:s})
        """.format(
                func_name, ",".join(func_args)
            )
        )
        return node.infer()

    def test_numpy_function_calls_inferred_as_ndarray(self):
        """
        Test that calls to numpy functions are inferred as numpy.ndarray
        """
        licit_array_types = (".ndarray",)
        for func_ in self.numpy_functions:
            with self.subTest(typ=func_):
                inferred_values = list(self._inferred_numpy_func_call(*func_))
                self.assertTrue(
                    len(inferred_values) == 1,
                    msg="Too much inferred value for {:s}".format(func_[0]),
                )
                self.assertTrue(
                    inferred_values[-1].pytype() in licit_array_types,
                    msg="Illicit type for {:s} ({})".format(
                        func_[0], inferred_values[-1].pytype()
                    ),
                )


if __name__ == "__main__":
    unittest.main()
