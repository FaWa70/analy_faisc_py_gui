
import matplotlib.pyplot as plt
import numpy as np


figurePlt4 = plt.figure()

arr_var = np.random.random(size=100)

figurePlt4.clear()

# ordre des colonnes : nb of image, Aeff, slope, bcenter[2], backg

# prepare the axis

axPlt3 = figurePlt4.add_subplot(221)
axPlt3.hist(arr_var, color='green', label='Aeff')
axPlt3.legend()
axPlt3.set_xlabel('Aeff in pixel')

axPlt4 = figurePlt4.add_subplot(222)
axPlt4.hist(arr_var, color='yellow', label='Slope')
axPlt4.legend()
axPlt4.set_xlabel('Slope (good if |slope| < 0.05 ')

axPlt5 = figurePlt4.add_subplot(223)
axPlt5.hist(arr_var, color='red', label="bcenter[2]")
axPlt5.legend()
axPlt5.set_xlabel('Maximum fluence in Grey Levels (GL)')

axPlt6 = figurePlt4.add_subplot(224)
axPlt6.hist(arr_var, color='blue', label='backg')
axPlt6.legend()
axPlt6.set_xlabel('Background in Grey Levels (GL)')

plt.show()
figurePlt4.tight_layout()
