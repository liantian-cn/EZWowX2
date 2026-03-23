import numpy as np

# 16x16 标记由 4 个 8x8 纯色块组成：
# +---------+---------+
# |    A    |    B    |
# | (15,25,20) (25,15,20)
# +---------+---------+
# |    B    |    A    |
# | (25,15,20) (15,25,20)
# +---------+---------+
_QUADRANT_LAYOUT: np.ndarray = np.array([[0, 1], [1, 0]], dtype=np.uint8)
_MARK_MASK: np.ndarray = np.kron(_QUADRANT_LAYOUT, np.ones((8, 8), dtype=np.uint8))

MARK8_TEMPLATE: np.ndarray = np.where(
    _MARK_MASK[..., None] == 0,
    np.array([15, 25, 20], dtype=np.uint8),
    np.array([25, 15, 20], dtype=np.uint8),
).astype(np.uint8)
