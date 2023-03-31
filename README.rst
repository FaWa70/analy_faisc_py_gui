analy_faisc_py_gui
##################

analy_faisc_py_gui, can be used to analyse spatial laser beam profiles.
It was written in the context of laser damage tests, where the
**effective surface area**, Aeff, and its fluctuations are needed to
calculate the peak fluence, Fmax, in the laser beam. Knowing the pulse energy
of a particular test, Ep, one then gets: Fmax = Ep / Aeff.


Obtaining the effective surface area from a beam image:
=======================================================
From the spatial beam profile, provided as greyscale image, one can get the
effective surface area in square pixel units simply by recognizing that, when
the sum over all greylevel values, sum(GL), corresponds to the pulse energy,
the GL of the brightest pixel, GLmax, corresponds to the peak fluence Fmax:

Aeff = Ep / Fmax = sum(GL) / Glmax * pixelsurface

However, this simple operation should be done after correction of the beam
image.

* Background correction:
The originally integer coded image needs to be converted to a float
representation. Then a constant can be subtracted to obtain noise fluctuating
around zero in regions where there is no light on the camera.

* Maximum correction:
The maximum pixel usually is a noise-affected pixel. It's thus better
to do some averaging or local fitting to determine the maximum GL to use


Getting information on fitted analytical beam models:
=====================================================


Published under the CeCILL-B FREE SOFTWARE LICENSE

GitHub repo:

Documentation: Some text on tab 5, but a lot of work is still necessary here.

