from __future__ import division

import numpy as np
from scipy.sparse import csr_matrix

from .kernels import KERNELS


def ndft(x, f_k):
    """Compute the nonuniform DFT

    Parameters
    ----------
    TODO

    Returns
    -------
    TODO

    See Also
    --------
    infft : inverse nonuniform FFT
    """
    x, f_k = map(np.asarray, (x, f_k))
    assert x.ndim == 1
    assert f_k.ndim == 1
    N = len(f_k)
    k = -(N // 2) + np.arange(N)
    return np.dot(f_k, np.exp(-2j * np.pi * x * k[:, None]))


def ndft_adjoint(x, f, N):
    """Compute the adjoint of the nonuniform DFT

    Parameters
    ----------
    TODO

    Returns
    -------
    TODO

    See Also
    --------
    infft : inverse nonuniform FFT
    """
    x, f = np.broadcast_arrays(x, f)
    assert x.ndim == 1
    k = -(N // 2) + np.arange(N)
    return np.dot(f, np.exp(2j * np.pi * k * x[:, None]))


def nfft_adjoint(x, f, N, sigma=5, tol=1E-8, m=None, kernel='gaussian',
                 use_fft=True, use_sparse=True):
    """Compute the inverse nonuniform FFT

    Parameters
    ----------
    TODO

    Returns
    -------
    TODO

    See Also
    --------
    indft : inverse nonuniform DFT
    """
    x, f = np.broadcast_arrays(x, f)
    assert x.ndim == 1

    N = int(N)
    n = N * sigma

    sigma = int(sigma)
    assert sigma >= 2

    kernel = KERNELS.get(kernel, kernel)

    if m is None:
        m = kernel.estimate_m(tol, N, sigma)
    assert m <= n // 2

    # Compute the (truncated) sum across the grid
    shifted = lambda x: -0.5 + (x + 0.5) % 1
    if use_sparse:
        col_ind = np.floor(n * x[:, np.newaxis]).astype(int) + np.arange(-m, m)
        val = kernel.phi(shifted(x[:, None] - col_ind / n), n, m, sigma)
        col_ind = (col_ind + n // 2) % n
        indptr = np.arange(len(x) + 1) * col_ind.shape[1]
        mat = csr_matrix((val.ravel(), col_ind.ravel(), indptr), shape=(len(x), n))
        g = mat.T.dot(f)
    else:
        x_grid = np.linspace(-0.5, 0.5, n, endpoint=False)
        g = np.dot(f, kernel.phi(shifted(x_grid - x[:, None]), n, m, sigma))

    # Compute the Fourier transform over this grid
    k = -(N // 2) + np.arange(N)
    if use_fft:
        ghat = n * np.fft.fftshift(np.fft.ifft(g))
        ghat = ghat[n // 2 - N // 2: n // 2 + N // 2]
        ghat *= np.exp(2j * np.pi * 0.5 * k)
    else:
        x_grid = np.linspace(-0.5, 0.5, n, endpoint=False)
        ghat = np.dot(g, np.exp(2j * np.pi * k * x_grid[:, None]))

    return ghat / kernel.phi_hat(k, n, m, sigma) / (sigma * N)