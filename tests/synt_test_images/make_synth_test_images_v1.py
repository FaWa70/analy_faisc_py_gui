"""
writes synthetic images to the disk
"""
import numpy as np
import matplotlib.pyplot as plt
from src.fitting_module_v2 import gauss2D_cst_offs, gaussEll2D_cst_offs
""" gauss2D_cst_offs.f(self, x_values, y_values, paras, offset=0)
paras = [vert_factor, x_shift, y_shift, waist_radius]"""
from imageio import imwrite

################ fix image size and bit-depth
x_max = 400
y_max = 300
z_fmt = "uint8"  # uint16 or uint8
z_max = np.iinfo(z_fmt).max
XX, YY = np.meshgrid(range(x_max), range(y_max))
# filenames contain the parameters:
# beamshape(rG) type(u8) backg(b25.2) ampl(a123.2) xCenter(x200.2) yCenter(y150.1) radius(r20.3)

# fixed paramters:
x_shift = 6 * x_max // 10  # 240
y_shift = 5 * y_max // 10  # 150

################ round Gaussians
# offset by backg
backg = z_max / 10
# three sizes: 1/e2 - radius = 20 40 60 px
for rad in [20, 40, 60]:
    vert_factor = 200
    waist_radius = rad
    ZZ = gauss2D_cst_offs.f(XX, YY, [vert_factor, x_shift, y_shift, waist_radius], offset=backg)
    ZZ = ZZ.astype(z_fmt)
    imwrite(("rG_" + z_fmt + "_b{:.1f}".format(backg)
             + "_a{:.1f}".format(vert_factor)
             + "_x{:.1f}".format(x_shift)
             + "_y{:.1f}".format(y_shift)
             + "_r{:.1f}".format(waist_radius)
             + ".tif"), ZZ)

# saturated three sizes: 1/e2 - radius = 20 40 60 px
# offset by backg
backg = z_max / 2
for rad in [20, 40, 60]:
    vert_factor = 200
    waist_radius = rad
    ZZ = gauss2D_cst_offs.f(XX, YY, [vert_factor, x_shift, y_shift, waist_radius], offset=backg)
    ZZ[ZZ > z_max] = z_max
    ZZ = ZZ.astype(z_fmt)
    imwrite(("rG_sat_" + z_fmt + "_b{:.1f}".format(backg)
             + "_a{:.1f}".format(vert_factor)
             + "_x{:.1f}".format(x_shift)
             + "_y{:.1f}".format(y_shift)
             + "_r{:.1f}".format(waist_radius)
             + ".tif"), ZZ)

################ elliptic Gaussians
# offset by backg
backg = z_max / 10
# three sizes: 1/e2 - radius = 20 40 60 px
for rad in [20, 40, 60]:
    vert_factor = 200
    waist_radius = rad
    # paras = [vert_factor, cent_x, cent_y, waist_rad_a, waist_rad_b, theta (degrees)]
    ZZ = gaussEll2D_cst_offs.f(XX, YY, [vert_factor, x_shift, y_shift,
                                        waist_radius * 1.5, waist_radius, 1.5 * rad], offset=backg)
    ZZ = ZZ.astype(z_fmt)
    imwrite(("ellG_" + z_fmt + "_b{:.1f}".format(backg)
             + "_a{:.1f}".format(vert_factor)
             + "_x{:.1f}".format(x_shift)
             + "_y{:.1f}".format(y_shift)
             + "_ra{:.1f}".format(waist_radius * 1.5)
             + "_rb{:.1f}".format(waist_radius)
             + "_th{:.1f}".format(1.5 * rad)
             + ".tif"), ZZ)

# saturated three sizes: 1/e2 - radius = 20 40 60 px
# offset by backg
backg = z_max / 2
# three sizes: 1/e2 - radius = 20 40 60 px
for rad in [20, 40, 60]:
    vert_factor = 200
    waist_radius = rad
    # paras = [vert_factor, cent_x, cent_y, waist_rad_a, waist_rad_b, theta (degrees)]
    ZZ = gaussEll2D_cst_offs.f(XX, YY, [vert_factor, x_shift, y_shift,
                                        waist_radius * 1.5, waist_radius, 1.5 * rad], offset=backg)
    ZZ[ZZ > z_max] = z_max
    ZZ = ZZ.astype(z_fmt)
    imwrite(("ellG_sat_" + z_fmt + "_b{:.1f}".format(backg)
             + "_a{:.1f}".format(vert_factor)
             + "_x{:.1f}".format(x_shift)
             + "_y{:.1f}".format(y_shift)
             + "_ra{:.1f}".format(waist_radius * 1.5)
             + "_rb{:.1f}".format(waist_radius)
             + "_th{:.1f}".format(1.5 * rad)
             + ".tif"), ZZ)

