# -*- coding: utf-8 -*-
"""
Created on Tue Dec  5 14:14:50 2017

@author: Wagner

This version can be executed from within spyder
"""

import sys
from PyQt5.QtWidgets import (QApplication, QWidget, QPushButton, QGridLayout,
                             QLabel, QFileDialog, QLineEdit)
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure # better do not use pyplot (but it's possible)

import numpy as np
import matplotlib.pyplot as plt
from scipy import optimize as opt
import numpy.polynomial.polynomial as poly
import math as ma
import time as ti

class Window(QWidget):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        ############      defining the widgets

        ### For loading the iamge file
        self.LbFileCaption = QLabel('Name of present file:')  # label (passive)
        self.LbFileName = QLabel('Click "Load File" to start')  # label (active)
        self.BtLoadFile = QPushButton('1. Load file')
        self.BtLoadFile.clicked.connect(self.Load_File)

        ### For plotting the image
        # a figure instance to plot the loaded image file
        self.figureIM = Figure()
        # this is the Canvas Widget that displays the `figure`
        # it takes the `figure` instance as a parameter to __init__
        self.canvasIM = FigureCanvas(self.figureIM)
        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbarIM = NavigationToolbar(self.canvasIM, self)

        ### For starting the effecive surface calculation
        # A button connected to `AeffCalc` method
        self.buttonAFC = QPushButton('2. Calc.Aeff')
        self.buttonAFC.clicked.connect(self.Calc_Aeff)

        ### For input of parameters
        self.LbPointsCaption = QLabel('Max. step number:')  # label (passive)
        self.EdPoints = QLineEdit('20')  # label (active)
        self.LbPixSizeCaption = QLabel('Linear pixel size (µm):')  # label (passive)
        self.EdPixSize = QLineEdit('1')  # label (active)

        ### For plotting the Aeff curve
        # a figure instance to plot the Aeff curve
        self.figureAFC = Figure()
        self.canvasAFC = FigureCanvas(self.figureAFC)
        self.toolbarAFC = NavigationToolbar(self.canvasAFC, self)


        ############      setting the layout
        grid = QGridLayout()
        grid.setSpacing(5) #defines the spacing between widgets
        # horizontally: end of label to edit, and vertically: edit to edit

        grid.addWidget(self.LbFileCaption, 0, 1, 1, 2)  # (object, Zeile, Spalte)
        grid.addWidget(self.BtLoadFile, 1, 0)  # (object, Zeile, Spalte)
        grid.addWidget(self.LbFileName, 1, 1, 1, 7)
        grid.addWidget(self.buttonAFC, 1, 8)

        grid.addWidget(self.canvasIM, 2, 0, 12, 4)
        grid.addWidget(self.toolbarIM, 15, 0, 1, 4)

        grid.addWidget(self.canvasAFC, 2, 4, 12, 4)
        grid.addWidget(self.toolbarAFC, 15, 4, 1, 4)

        grid.addWidget(self.LbPointsCaption, 2, 8)
        grid.addWidget(self.EdPoints, 3, 8)
        grid.addWidget(self.LbPixSizeCaption, 4, 8)
        grid.addWidget(self.EdPixSize, 5, 8)

        self.setLayout(grid)
        # grid.setRowStretch(2, 1)

        ############      Define window size etc.
        self.setGeometry(300, 300, 900, 500)
        self.setWindowTitle('AeffV1bS')
        self.show()


    def Load_File(self):
        '''load the image file and show it in the left pane'''
        # choose the image with a dialog
        fname = QFileDialog.getOpenFileName(self, 'Open file',
         'D:\\RECHERCHE\\Calculations\\LaserD - analyse image faisceau\\v1 Aire eff etc from imageFaisc\\Aeff etc python v1')

        # load the image
        global image
        if fname[0]: # a file was chosen
            image = plt.imread(fname[0])

        # display the filename in the label
        self.LbFileName.setText(fname[0])

        # Clear the image from earlier uses
        self.figureIM.clear()

        # Display the image
        axIM = self.figureIM.add_subplot(111)
        axIM.axis("off")
        axIM.imshow(image, cmap='jet')
        cax = axIM.imshow(image, cmap='jet')
        # common color maps: gray, hot, hsv, jet, gist_ncar
        self.figureIM.colorbar(cax, orientation='horizontal')
        # si c'est un widget, il faut le self. devant
        # self.figureIM.tight_layout()

        ### check for saturation
        # Normalize full data range to 1 and convert pixel values to float
        image = image / np.iinfo(image.dtype).max
        print('IMAGE WAS NORMALIZED AND CONVERTED')
        print('Pixel values are now of type: ', image.dtype )
        print('The shape of the image data is: ', image.shape )
        print('Maximum pixel value of the normalized image: ', image.max() )
        if image.max() >= 1:
            print('THIS IMAGE IS SATURATED!')
            axIM.text(10,20,'THIS IMAGE IS SATURATED')
        else:
            print('The image is not saturated!')
            axIM.text(10,-20,'OK')
        print(' ')

        # refresh canvas
        self.canvasIM.draw()


    def Calc_Aeff(self):
        ''' Calculate the effective surfaces '''
        global image

        # read input edits
        points = eval(self.EdPoints.text())
        pixelSize = eval(self.EdPixSize.text())
        PixSurface = pixelSize*pixelSize  # Surface d'un pixel (µm²).
        # a*a is faster than a**2

        #%% Make first run of Aeff curve - down to the first guess for minIdx

        t1 = ti.perf_counter()
        t2 = ti.process_time()

        # number of pixels to crop on each side at each iteration
        step = int(np.min(image.shape)/(2*points))-1
        # set automatically to be able to make the desired no of points

        count = 3
        if points > 3:
            count = points # le nombre maximal de points sur la courbe

        PixMaxS = np.zeros(count) # line vector
        # PixMaxS = np.zeros((count,1)) # column vector
        PixSumS = np.zeros(count) # line vector
        AeffS = np.zeros(count) # line vector
        ImSize = np.zeros(count) # line vector
        droiteParS = -1e50 * np.ones((count-2,2))

        ## si on veut le plot avant fit
        #fig2 = plt.figure() #create figure object (define fig size)
        #ax2 = fig2.add_subplot(111) # add axes (one row , one col, plot num 1)
        ## ax2.plot(ImSize,AeffS, 'ob', ms=5, label='first run')
        #ax2.set_xlabel('Square pixels in software aperture');
        #ax2.set_ylabel('Pix_Sum');

        Taille = image.shape
        Continue = True
        while (Taille[0]-step > step) & (Taille[1]-step > step) & (count > 0) & Continue:
            usedimage = image[step:Taille[0]-step, step:Taille[1]-step ]
            # on enleve une partie de l'image

            Taille = usedimage.shape
            ImSize[count-1] = Taille[0] * Taille[1]
            # nombre de pixels dans l'image coupé % si on veut le plot

            PixMaxS[count-1] = usedimage.max()  # Pixel maximal
            PixSumS[count-1] = np.sum(usedimage)
            # Calcul de la somme des Pixels (correspond à Energie du pulse)

            #ax2.plot(ImSize[count-1],PixSumS[count-1], 'ob', ms=5, label='first run')

            if points - count > 1:
                # il faut au moins 3 points pour calculer la droite par polyfit

                # 1. Find the parameters of the lines going though the last points
                droiteParS[count-1, :] = poly.polyfit(ImSize[count-1:], PixSumS[count-1:], 1)
                # droiteParS[indx,0] est le offset a ImSize = 0
                # droiteParS[indx,1] est la pente

                # 2. Calculer les deviations du dernier point de la droite
                # 3.b) Déduire un critère
                # arreter si la deviation relative du nouveau point de la droite fait
                # plus que 10%
                theoPixSum = (droiteParS[count-1,1]*ImSize[count-1] + droiteParS[count-1,0])
                Continue = (abs(theoPixSum)- PixSumS[count-1]) / theoPixSum < 0.05

                #ax2.plot(ImSize[count-1],PixSumS[count-1], 'ro', ms=6, markerfacecolor='none', label='line calculated')
                #ax2.plot(ImSize[count-1],theoPixSum, 'ko', ms=6, markerfacecolor='none', label='theoPixSum')

            count = count-1

        minIdx = count + 1 # eventuellement c'est mieux de faire count + 1 ici.
        memCo = minIdx # memoire du premier essai de minIdx



        #%% Try to increase minIdx and make the final calculation

        # Prepare Aeff curve plot
        # clear the plot of the last run
        self.figureAFC.clear()
        # create the AeffCourve axis
        axAFC = self.figureAFC.add_subplot(111)
        axAFC.set_xlabel('Square pixels in software aperture');
        axAFC.set_ylabel('$A_{eff}$');


        # Check the sub function and show the primary good data range
        #def AeffCurveBasic(offset, image, points=5, step=5, PixSurface=1, imBackground='absent'):
        GoodAeffs = AeffCurveBasic(0, image, len(AeffS)-minIdx, step, PixSurface)
        GoodImSiz = ImSize[minIdx:]
        axAFC.plot(GoodImSiz,GoodAeffs, 'ro', ms=5, markerfacecolor='none', label='Good points')

        if minIdx > len(AeffS)-3:
            print('Error: fit impossible: minIdx > length(AeffS)-3')
        else:
            if 1.5 * minIdx > len(AeffS)-3:
                print('Warning: fit of curved line: 1.5 * minIdx > length(AeffS)-3')
            else:
                # Ils restent au moins 3 points qui definissent la droite
                # l'image est bien, on cherche le bruit-offset qui minimise la pente
                minIdx = ma.floor(1.5 * minIdx)

            #Calcul du Bruit moyen sur une petite zone (1/10ieme) qui doit être noir
            BruitMoyen = np.mean(image[0:ma.floor(image.shape[0]/10),1:ma.floor(image.shape[0]/10)])
            # point du départ du fit: correction par le bruit moyen sur la petite zone

            # def mertit_Aeff_slope_Sq(offset, image, points=5, step=5,
            #                             PixSurface=1, imBackground='absent'):
            # Returns the square of the slope of the line fitted to the outer
            # Aeff data points.
            useSteps = len(AeffS)-minIdx
            fitRes = opt.minimize(mertit_Aeff_slope_Sq, x0=(BruitMoyen), args=(image, useSteps, step, PixSurface) )

            # montrer et sortir le resultat
            # print('Best noise value = ', fitRes.x[0])
            GoodAeffs = AeffCurveBasic(fitRes.x[0], image, memCo, step, PixSurface)
            GoodImSiz = ImSize[-memCo:]
            axAFC.plot(GoodImSiz,GoodAeffs, '*g', ms=5, label='After offset correction')
            axAFC.plot(GoodImSiz[-useSteps:],GoodAeffs[-useSteps:], '*r', ms=5, label='points used for fit')

            droiteParS = poly.polyfit(GoodImSiz[-useSteps:],GoodAeffs[-useSteps:],1)
            #fit a line on the good data to get an idea of the uncertainty
            axAFC.plot([0, ImSize.max()],[droiteParS[0], droiteParS[1]*ImSize.max()+droiteParS[0]], '--k', label='result')
            axAFC.text(GoodImSiz[-useSteps],GoodAeffs[-useSteps]*1.1,'A_eff = {:.1f}'.format(GoodAeffs[-useSteps]))
            axAFC.legend(loc='best')

            # Write output values
            NoiseBorder = useSteps*step # in pixels
            PiMax = (image-fitRes.x[0]).max()
            PiSum = np.sum(image-fitRes.x[0])
            BruitOffset = fitRes.x[0]
            RelVar = np.abs(GoodAeffs[-1]-GoodAeffs[-useSteps])/GoodAeffs[-useSteps]
            Aeff = GoodAeffs[-useSteps]

            print('RESULTS:')
            print('The best offset correction is: ', BruitOffset )
            print('The sum of the pixel values (treated image) is: ', PiSum )
            print('The maximum pixel value of the treated image is: ', PiMax )
            print('Aeff = ', Aeff)
            print('Pixel size was = ', pixelSize)
            print('The relative uncertainty of Aeff is: ', RelVar )
        # end block: if minIdx is ok

        print(' ')
        print('Elapsed time was: ',ti.perf_counter() - t1, " s")
        print('Process time was: ',ti.process_time() - t2, " s")
        print('This was version 2 (fast)')
        print('------------------------')

        # refresh canvas
        self.canvasAFC.draw()

####################################################
def AeffCurveBasic(offset, image, points=5, step=5, PixSurface=1, imBackground='absent'):
    """ Returns only the outermost points of the Aeff curve.
    :param offset:
    :param image:
    :param points: points=5 # default of optional parameter, but should be passed
    should be the same as in calling function
    :param step: step=5 # default of optional parameter, but should be passed
    should be the same as in calling function
    :param PixSurface: PixSurface=1 # default of optional parameter (if =1, Aeff is in pixels)
    should be the same as in calling function
    :param imBackground: imBackground = 'absent' # default of optional parameter
    :return: AeffS - vector of length 'points' (or less)
    """

    PixMaxS = np.zeros(points) # line vector
    PixSumS = np.zeros(points) # line vector
    AeffS = np.zeros(points) # line vector

    if imBackground != 'absent':
        image = image - imBackground
    image = image - offset

    Taille = image.shape
    while (Taille[0]-step > step) & (Taille[1]-step > step) & (points > 0):
        usedimage = image[step:Taille[0]-step, step:Taille[1]-step ]
        # on enleve une partie de l'image

        Taille = usedimage.shape

        PixMaxS[points-1] = usedimage.max() # Pixel maximal
        PixSumS[points-1] = np.sum(usedimage)
        # Calcul de la somme des Pixels (correspond à Energie du pulse)
        AeffS[points-1] = PixSumS[points-1] * PixSurface/ PixMaxS[points-1];

        points = points-1
    return AeffS
###########################

def mertit_Aeff_slope_Sq(offset, image, points=5, step=5, PixSurface=1, imBackground='absent'):
    # Returns the square of the slope of the line fitted to the outer
    # Aeff data points.
    # For parameter explanation see AeffCurveBasic
    xBidon = np.arange(points)
    Aeffs = AeffCurveBasic(offset, image, points, step, PixSurface, imBackground)
    droiteParS = poly.polyfit(xBidon,Aeffs,1)
    return droiteParS[1]**2

####################################################
if __name__ == '__main__':
    # app = QApplication(sys.argv) # std : create QApplication
    app = QApplication.instance() # checks if QApplication already exists
    if not app: # create QApplication if it doesnt exist
        app = QApplication(sys.argv)
    app.aboutToQuit.connect(app.deleteLater)

    main = Window()
    main.show()

    # sys.exit(app.exec_()) # std : exits python when the app finishes
    app.exec_() #do not exit Ipython when the app finishes
