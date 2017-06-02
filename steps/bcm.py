#!/usr/bin/env python3

"""
Code adapted from these examples:
https://lubosz.wordpress.com/2014/05/27/gstreamer-overlay-opengl-sink-example-in-python-3/
https://github.com/peterderivaz/pyopengles
https://github.com/gasman/shortcrust/
"""
import ctypes

from ctypes import c_int, c_uint, c_int32, c_uint32, c_int16, c_uint16, c_void_p, POINTER

_init_called = False

try:
    _lib = ctypes.CDLL('libbcm_host.so')
except OSError:
    raise ImportError("Bcm unavailable, this needs to run on a Raspberry Pi")

bcm_host_init = _lib.bcm_host_init
bcm_host_init.argtypes = []
bcm_host_init.restype = None


def ensure_init():
    global _init_called
    if not _init_called:
        _init_called = True
        bcm_host_init()


class Alpha_struct(ctypes.Structure):
    """typedef enum {
  /* Bottom 2 bits sets the alpha mode */
  DISPMANX_FLAGS_ALPHA_FROM_SOURCE = 0,
  DISPMANX_FLAGS_ALPHA_FIXED_ALL_PIXELS = 1,
  DISPMANX_FLAGS_ALPHA_FIXED_NON_ZERO = 2,
  DISPMANX_FLAGS_ALPHA_FIXED_EXCEED_0X07 = 3,
  DISPMANX_FLAGS_ALPHA_PREMULT = 1 << 16,
  DISPMANX_FLAGS_ALPHA_MIX = 1 << 17
} DISPMANX_FLAGS_ALPHA_T;
typedef struct {
  DISPMANX_FLAGS_ALPHA_T flags;
  uint32_t opacity;
  VC_IMAGE_T *mask;
} DISPMANX_ALPHA_T;
typedef struct {
  DISPMANX_FLAGS_ALPHA_T flags;
  uint32_t opacity;
  DISPMANX_RESOURCE_HANDLE_T mask;
} VC_DISPMANX_ALPHA_T;  /* for use with vmcs_host */
"""
    _fields_ = [("flags", ctypes.c_long),
                ("opacity", ctypes.c_ulong),
                ("mask", ctypes.c_ulong)]


DISPMANX_PROTECTION_NONE = 0

c_uint32_p = POINTER(c_uint32)
DISPMANX_ELEMENT_HANDLE_T = c_uint32


class EGL_DISPMANX_WINDOW_T(ctypes.Structure):
    _fields_ = [("element", DISPMANX_ELEMENT_HANDLE_T), ("width", c_int), ("height", c_int)]


EGLNativeWindowType = POINTER(EGL_DISPMANX_WINDOW_T)


def c_ints(L):
    # from https://github.com/peterderivaz/pyopengles/blob/master/pyopengles.py#L40
    return (ctypes.c_int * len(L))(*L)


def create_native_window(x, y, width, height, layer=0, screen=0, alpha_flags=0, alpha_opacity=0):
    alpha_s = Alpha_struct(alpha_flags, alpha_opacity, 0)

    dst_rect = c_ints((x, y, width, height))
    src_rect = c_ints((0, 0, width << 16, height << 16))

    dispman_display = _lib.vc_dispmanx_display_open(screen)
    dispman_update = _lib.vc_dispmanx_update_start(screen)
    dispman_element = _lib.vc_dispmanx_element_add(dispman_update, dispman_display,
                                                  layer, ctypes.byref(dst_rect),
                                                  screen, ctypes.byref(src_rect),
                                                  DISPMANX_PROTECTION_NONE,
                                                  alpha_s, 0, 0)  # alpha clamp transform

    _lib.vc_dispmanx_update_submit_sync(dispman_update)
    window = EGL_DISPMANX_WINDOW_T(dispman_element, width, height)

    return window


def get_resolution(screen=0):
    width, height = ctypes.c_int(), ctypes.c_int()
    _lib.graphics_get_display_size(screen, c_uint32_p(width), c_uint32_p(height))
    return width.value, height.value
