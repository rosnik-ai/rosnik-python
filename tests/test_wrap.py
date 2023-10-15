"""We test wrap_class_method via test_openai."""

from rosnik import wrap


def test_get_stack_frames():
    frames = wrap.get_stack_frames(3)
    assert len(frames) == 3


def test_get_stack_frames__false():
    frames = wrap.get_stack_frames(3, use_get_frame=False)
    assert len(frames) == 3
