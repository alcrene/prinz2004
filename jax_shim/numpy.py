"""
Helper classes for writing fully compatible NumPy/JaX code.
The goal is that code written for JaX should degrade gracefully to using pure
NumPy operations if JaX is unavailable. (Or turned off, e.g. for profiling.)

We expect users who want this graceful degradation to also use the high-level
`jax.numpy` module. This makes our problem already 99% solved, since for most
things we can just redirect ``jnp.<op>`` to ``np.<op>``.

.. Important:: The array type created with `jnp.array` is a subclass of the
   standard NumPy array, augmented with additional JaX methods. This is what
   allows operations like ``A.at[idx].set(value)`` to be transparently
   translated to a NumPy-compatible form.

"""

import numpy as np

def __getattr__(attr):
    return getattr(np, attr)

## Array with .at method ##
# C.f. https://numpy.org/doc/stable/user/basics.subclassing.html#slightly-more-realistic-example-attribute-added-to-existing-array

class array(np.ndarray):
    """
    Substitute for `numpy.array` which adds the `at` method for
    purely-function in-place operations.
    """
    def __new__(cls, input_array):
        obj = np.asarray(input_array).view(cls)
        obj.at = _AtConstructor(obj)
        return obj
    def __array_finalize__(self, obj):
        if obj is None: return
        at_constructor = getattr(obj, "at", None)
        if at_constructor is None:
            # (Probably) attaching an `.at` method to a plain NumPy array: we need to create a new one
            self.at = _AtConstructor(obj)
        else:
            self.at = at_constructor

class _AtConstructor:
    def __init__(self, owner):
        self.owner = owner
    def __getitem__(self, key):
        return _AtOp(self.owner, key)
        
class _AtOp:
    def __init__(self, owner, key):
        self.owner = owner
        self.key = key
    def set(self, value):
        self.owner[self.key] = value
    def add(self, value):
        self.owner[self.key] += value
