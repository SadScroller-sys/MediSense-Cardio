"""Test of the orientation step of the demo pipeline (a photo taller than wide is turned a quarter turn counter-clockwise). Run: python -I demo/tests/test_orient.py"""
import os
import sys

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
import pipeline as P  # noqa: E402


def test_upright_photo_is_turned():
    img = np.zeros((400, 300, 3), np.uint8)
    img[0, :, 2] = 255                                   # a red row on the top edge
    out, turned = P.orient(img)
    assert turned and out.shape[:2] == (300, 400)
    assert out[:, 0, 2].min() == 255                     # counter-clockwise: the top edge becomes the left edge


def test_landscape_photo_is_left_alone():
    img = np.zeros((300, 400, 3), np.uint8)
    out, turned = P.orient(img)
    assert not turned and out is img


def test_square_photo_is_left_alone():
    img = np.zeros((300, 300, 3), np.uint8)
    assert not P.orient(img)[1]


if __name__ == "__main__":
    n = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_") and callable(fn):
            fn()
            n += 1
            print("ok  ", name)
    print(n, "tests passed")
