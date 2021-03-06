from abc import ABCMeta, abstractmethod, abstractproperty

import numpy

__all__ = [
    "BaseRelativePermeability",
]


# See <https://stackoverflow.com/questions/35673474/using-abc-abcmeta-in-a-way-it-is-compatible-both-with-python-2-7-and-python-3-5>
ABC = ABCMeta("ABC", (object,), {"__slots__": ()})


class BaseRelativePermeability(ABC):
    """Base class for relative permeability models. Do not use."""

    _id = None
    _name = ""

    def __init__(self, *args):
        pass

    def __repr__(self):
        out = [
            "{} relative permeability model (IRP = {}):".format(self._name, self._id)
        ]
        out += [
            "    RP({}) = {}".format(i + 1, parameter)
            for i, parameter in enumerate(self.parameters)
        ]
        return "\n".join(out)

    def __call__(self, sl):
        if numpy.ndim(sl) == 0:
            if not (0.0 <= sl <= 1.0):
                raise ValueError()
            return self._eval(sl, *self.parameters)
        else:
            sl = numpy.asarray(sl)
            if not numpy.logical_and((sl >= 0.0).all(), (sl <= 1.0).all()):
                raise ValueError()
            return numpy.transpose([self._eval(sat, *self.parameters) for sat in sl])

    @abstractmethod
    def _eval(self, *args):
        raise NotImplementedError()

    def plot(self, n=100, ax=None, figsize=(10, 8), plt_kws=None):
        """Plot relative permeability curve.

        Parameters
        ----------
        n : int, optional, default 100
            Number of saturation points.
        ax : matplotlib.pyplot.Axes or None, optional, default None
            Matplotlib axes. If `None`, a new figure and axe is created.
        figsize : array_like or None, optional, default None
            New figure size if `ax` is `None`.
        plt_kws : dict or None, optional, default None
            Additional keywords passed to :function:`matplotlib.pyplot.plot`.

        """
        import matplotlib.pyplot as plt

        if not (isinstance(n, int) and n > 1):
            raise TypeError()
        if not (ax is None or isinstance(ax, plt.Axes)):
            raise TypeError()
        if not (figsize is None or isinstance(figsize, (tuple, list, numpy.ndarray))):
            raise TypeError()
        if len(figsize) != 2:
            raise ValueError()
        if not (plt_kws is None or isinstance(plt_kws, dict)):
            raise TypeError()

        # Plot parameters
        plt_kws = plt_kws if plt_kws is not None else {}
        _kwargs = {"linestyle": "-", "linewidth": 2}
        _kwargs.update(plt_kws)

        # Initialize figure
        if ax:
            ax1 = ax
        else:
            figsize = figsize if figsize else (8, 5)
            fig = plt.figure(figsize=figsize, facecolor="white")
            ax1 = fig.add_subplot(1, 1, 1)

        # Calculate liquid and gas relative permeability
        sl = numpy.linspace(0.0, 1.0, n)
        kl, kg = self(sl)

        # Plot
        ax1.plot(sl, kl, label="Liquid", **_kwargs)
        ax1.plot(sl, kg, label="Gas", **_kwargs)
        ax1.set_xlim(0.0, 1.0)
        ax1.set_ylim(0.0, 1.0)
        ax1.set_xlabel("Saturation (liquid)")
        ax1.set_ylabel("Relative permeability")
        ax1.grid(True, linestyle=":")

        plt.draw()
        plt.show()
        return ax1

    @property
    def id(self):
        """Return relative permeability model ID in TOUGH."""
        return self._id

    @property
    def name(self):
        """Return relative permeability model name."""
        return self._name

    @abstractproperty
    def parameters(self):
        raise NotImplementedError()

    @parameters.setter
    def parameters(self, value):
        raise NotImplementedError()
