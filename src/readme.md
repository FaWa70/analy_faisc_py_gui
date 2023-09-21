# Next steps...
- Bugs:
  * If tab 4 used, is auto dark image detection working?
  * If color-zoom on tab 1 is used, the image on tab 2 is 
    invisible
  * Some labels display rich text Aeff some don't. In fact having
    html style text in combo boxes is complicated (see htmlwidgets.py
    downloaded from https://apocalyptech.com/linux/qt/qcombobox_html/) In table headers may be too.
  * Using the fitted max for Aeff calc does not seem to work
  * The fit parameter history does not work
  * There may be a problem with the statistics of the 
    elliptical fit (analyze "pieds...wcf" file)
  
- Bad programming style:  
Uses partially global variables for the filenames of the 
xlsx files (and their directories)
- In the 'user manual' tab: Continue, Subtitles...
- In the z-variation tab implement the possibility to get the 
data from earlier saved excel files.
- When changing to tab2/cross-sections, plot both models. 
Thereafter only plot the ones that are fitted.
- Implement the "straightness" parameter of the Aeff curve. 
Ideas? Possibly: 
(ym-yd)**2 / yd moyenné (ou max?) sur tout les points utilisés 
pour la droite. Mais ça reste à voir.

- Make columns of table on tab 2 narrower 
(set_fixed_width was tried, but better use fontmetrics to 
keep space for output typically <4.3 digits and header) 

# Ideas:
- In tab2, *add the evaluation of D4sigma values* for round or elliptical spots. 
For the formulas, see: https://en.wikipedia.org/wiki/Beam_diameter 
- Add the possibility to export a nice representation of the beam that can 
be used in reports and papers. This needs a scale! (2D, 3D). 
Maybe on tab2 or a new one inbetween 2 and 3? Until then do it in Gwyddion.
- In tab 4, *add w(z) fits with M² parameter* 
(How to choose the data to use? Allow outlier removal?) 
- Add a tab with a short user manual... *started tab5* but has problems with 
picture display
- Tab2 Add automatic zoom on cross-sections: all, beam, maximum. 
Or keep manual zoom when changing image.
- Tab2 Add thresholded surface measurement (*done*), maybe even with 
shape fit (rectangle, circle)
- Tab3 and 4, in exported file display a warning if the image (or the stack) 
contains saturated pixels
- In tab2, transform the vertical condition GL > FitLimit to a similar 
horizontal condition. The vertical condition uses only upper 
noisy data on the border of the good zone.
- Implement masking of pixels in tab1 and 2, with interpolation under it.
- Add calculation of the uncertainty in Aeff for every image: 
The maximum from a mean or a fit gets an uncertainty. The 
uncertainty of the energy depends on the uncertainty in the offset,
which is again a mean or a fit result. Then a weighted mean with
uncertainty can be calculated.

# Versions:
## Version 6:
Scans through z-values if the folders have readable z information.
(Maybe also ok for wcf file names)

## Version 5:
With possibility to select data for histograms.

## Version 4:
The export works completely (with choice of columns) and 
statistics lines.

## Version 3:
The export works, but all colums of `results`
are exported.

## Version 2:
Is the start of the full version, based on `analy_fluo`.

Functionality description see below. 

## Version 1b: 
Plots the Aeff-curve 
and gives output in the console 


# Version 2: Usage
## In tab 1: Load and pre-process images
* Load a set of images (one wcf-file, the image size is 
automatically detected) or image files of same shape
in a single folder. The shape is defined by the initially 
chosen file. 
* Select the interesting part of these images by cropping 
laterally, but do not crop too close as you 
need pixels for the background. 
* Median Filter a bit to reduce noise fluctuations or dead pixels.
* Select a large roi for background subtraction (The roi 
separates the region with energy (beam) form the region 
without energy (background)). For selecting the roi: check "redefine",
then click the image, position on one corner and hit "h" on the 
keyboard, position on the second corner and hit "n" on the keyboard, 
done.
* Define the range of good images in the stack. If the 
start n° is larger than the stop n°, the range between these 
two is excluded from tab 2 and 3. Dark images should be excluded
but one of them can be used to be subtracted from all valid images.

Maybe implemented later: Mask pixels from dust particles or broken 
camera pixels. (See black image (if existing) to mask also in the 
region of the beam.) 
To enable for zooming and dezooming by cropping (for precise
masking of dead camera pixels) I switched to absolute coordinates
for the masked pixels and the ROI. BUT maybe this was useless as 
zooming with the toolbar zoom-tool does tha same.
Masking only makes sense (in terms of energy) when the masked 
points are interpolated instead of being ignored, right?

## In tab 2: Full analysis of one image
* Choose how to make the background correction.

## In tab 3: Statistics and export
* Analyze all chosen images
* Display the results (histograms)
* Export to Excel

# Version 2: programming remarks
## Global variables
Many global variables are used. The numbers at the end usually refer
to the tab number where the variable is used
 
### global `imStack`
Inherited from `analy_fluo`.
3D nd-array: is of type float from the beginning, the last index chooses 
the image, the first index is the row (y) index, the second is the column
(x) index.  

### global `roiS`
Inherited from `analy_fluo`.
Matrix: has to be float if not, there is no "nan". The first index is 
the RoiNo (rowNo). The second index is: xfrom, xto, yfrom, yto 
(all in one line).  Only line 0 is used here (and may be laser line 2 
if masking will be activated). The roi is used to indicate the limit 
between the beam and teh background. 
#### Conventions: 
1st line = index 0 = Outside is the background 

2nd line = not used here

3nd line = index 2 = Inside is _temporarily_ the new zone to be 
modified when in mask editing mode

4th line = not used here

### global `res_arr`
Matrix: `len(good_idx)` rows and as many columns as there are 
quantities to export in the excel file

## Program flow:
### Tab 2:
The auto-crop function needs a separation of lateral operations and 
vertical operations on the image: 
`self.get_step()` --> global step; global frame_width.   
`frame_width` is necessary before making the auto-crop.

`self.make_auto_crop()` --> global im_to_show2; global auto_crop_uly, 
auto_crop_ulx.  
`im_to_show2` is the image to work with in tab 2

`self.get_backg()` --> global backg; global energy;  
global im_to_show2.  
Makes the background correction on `im_to_show2`. Calls 
make_auto_crop_dark if needed (if a dark image is used)
Also published backg and energy (the sum of the corrected image).

`self.get_beam_center()` --> global bcenter.  
Find the maximum of the beam. Uses the method chosen in the upper
right combo-box. This may later involve fitting.

`self.Aeff_Tb_calculations()`  
Fills the upper table on the right

`self.display2()`  
Fills the 2D display on the left

`self.plot2_1D()`  
Fills the 1D display in the middle


# Comments on tested programming routines
## Updating the images when moving the slider
The initial versions clears the figure and recreates the axes and all
objects in it at each call of `showIm1`. I thought this was the reason 
for rather slow update, but keeping the same cax just updating it with 
`cax.set_data` did not accelerate a lot. Maybe because a new set of white 
lines is added (at each call) instead of the old set being updated.

In Stackoverflow people use multi-threading and other advanced stuff to 
accelerate this kind of tasks.

## Fitting with mean initialization or with 0 initialization?
With mean initialization it is approximately 0.5 s faster. 
Uses "minimize", could also use "scalar_minimize" for more speed.

# The roles of the functions in MyTableWidget

## General functions

  ### `__init__(self, parent)`:
  Creates the TableWidget (`tabs`) and the pages (`tab1`, `tab2` etc) 
  
  ### `add_widgets_to_tab1()`:  Load and pre-process
  Creates the elements of the first tab (`tab1`) and connects them 
  to their methods. This is a _local function of `__init__`_ and is called 
  only by `__init__`. The purpose of the function is to structure the code 
  (and be able to fold it).
  
  ### `set_layout_of_tab1()`: Load and pre-process
  Sets the positions of the elements of the first tab (`tab1`) on a 
  grid layout. As `add_widgets..` This is a _local function of `__init__`_
  and is called  only by `__init__`. 
  The purpose of the function is to structure the code 
  (and be able to fold it).
       
## Methods of `tab1` : Load and pre-process

  ### `display_down(self)`:
  Is connected to `BtNumDwn` and does the same as arrow down or arrow left 
  on the slider: It reduces the value of the slider by one (if possible). 
  This change of the slider value automatically 
  fires the `SlNum.valueChanged` event which is connected to the 
  `display` method  
  
  ### `display_up(self)`:
  Is connected to `BtNumUp` and does the same as arrow up or arrow right 
  on the slider: It increases the value of the slider by one (if possible). 
  This change of the slider value automatically 
  fires the `SlNum.valueChanged` event which is connected to the 
  `display` method  
   
  ### `Load_File1(self)`:
  Deals with the file names of the stack of images. It defines the 
  global variables `dirname`, `baseName`, `f_name`.
  Launches `load_stack`.
 
  ### `load_stack(self)`:
  Fills the global ndarray `imStack` with the wanted images but also 
  publishes the global variables `sat_value`, `im1_width`, `im1_height` 
  For wcf-files with 64 images: 
  * It finds the image resolution from the
  file-size.
  * Reads the images from the file while updating the progress-bar
  * Deletes the outermost pixels (variable `cm` (crop-margin)) because 
  this contains a (nearly) saturated pixel (hidden data?).
  
  The fist time it initializes the spin boxes for cropping 
  (based on the image size), the ROIs (to NAN), and the list of masked 
  pixels (to empty list).
  
  Crops laterally if CbCropped is ckecked
  
  The calls `get_sat_pixels`, `showRoiS` and `display` (in this order)
    
  ### `get_sat_pixels(self)`:
  Uses self.LbPixSat to display the number of images that 
  contain saturated pixels and the number of saturated pixels in
  `imStack`.
    
  ### `showRoiS(self)`:
  Displays the present roi status in the labels.     

  ### `set_crop_margins(self)`:
  Is connected to the margin spin boxes `SbXXXX.valueChanged`.
  Essentially calls `display`, but also uses `sender` to make sure the 
  upper limit is always the upper limit by adjusting the ranges of the 
  spinboxes. 
  
  ### `display(self)`:
  Is connected to the `SlNum.valueChanged` event that is also fired at 
  startup (before the necessary variables for display are defined). 
  That's why `display` captures the `NameError` exception. If there is 
  no `NameError` it:
  
  If the filter preview is active: calls the special display function 
     `display_MedFi_preview`.
     
  Else: calls `self.showIm1` with the right image of the stack.
  
  ### `showIm1(self, ImToShow)`:
  Makes the drawing of the picture (`ImToShow`) on the canvas after 
  modifying the masked pixels (if mask display is on). 
  Superposes lines for the crop margins (if the images are not cropped) 
  and the ROI by calling `UpdateLinesIm1`. 
  
  ### `UpdateLinesIm1(self, xM =-10, yM = -10)`:
  Deletes and redraws the lines on `axIM1` according to the crop status and 
  the content of `roiS` and the roi checkboxes. Draws a cross when waiting 
  for the first (upper left point `h`, or a single point `b`) 
  and a box when waiting for the second (lower right point `n`).
  Chooses different colors for the different ROIs. 
  Also draws the selection for the mask modifications, but this one is not 
  redrawn if the image is changed. 
  
  ### `modify_mask(self)`:
  Called by `GetKeyIm1` if mask modification active and selection finished.
  Adds or removes the third line of 'roiS' to 'masked' pixels (list of tuples).
  Uses sets for this.
    
  ### `roi_def(self)`:  
  Called by the roi checkboxes sets the value of globals `roiS` and `roiNo`.
  chooses the line in the roiS array and sets that line to nan. (That's the 
  reason why roiS is in of type float.)
  
  ### `GetMouseIm1(self, event)`:
  Manages the drawing of the lines depending on the mouse position.
  Exits on useless events. Calls `UpdateLinesIm1` on useful events. 
  
  ### `GetKeyIm1(self, event)`:
  defines the rois using the keys: `h` for the upper left corner and 
  `n` for the lower right corner. 
  Modifies the contents of the global `roiS` (x_min, x_max, y_min, y_max) 
  Modifies the roi checkboxes.
        
  ### `crop_or_uncrop(self)`:
  Is connected to `CbCrop.stateChanged`.
  Applies the crop margins to the image stack `imStack` and `showIm1`
  displays the zoomed view without the white lines. 
  If the crop margins shall be modified, one first needs
  to untick the checkbox (and wait until the full images are reloaded), 
  modify, and retick the checkbox.
  
  ### `medFi_state_changed(self)`:
  Connected to the `rdbtgroupMedFi.buttonClicked[int]` event. 
  
  0: Tries to restore the backup of `imStack` (see button 2) and calls
  `display`.
  
  1: Calls `display_MedFi_preview` when entering the preview state.
  
  2: Applies the filter to all images of the stack, but, before, makes a 
  backup (`oldStack`) of `imStack` (except if they are already 
  equal).
  
  ### `medFi_sb_changed(self)`:
  Connected to the spinbox `SbMedFi.valueChanged` event. 
  
  Calls `display_MedFi_preview(self)` if MedFi preview is on.
  
  ### `display_MedFi_preview(self)`:
  Called by `MedFi_state_changed(self)`, `medFi_sb_changed(self)`, and 
  `display(self)` (if MedFi preview is on).
  
  Calls `showIm1` with the filtered present image. Is quite fast.

## Methods of `tab2` : Full analysis of one image
  ### `plot_graphs(self)`:
  Called by `bt_plot_now`.
  Defines a binary mask from the information in 'Region', 'Out/In' and 
  'Mask'. 
  Chooses the right function from the information in 'Value'. 
  Plots the graphs on canvas2.
  
  ### `export_graphs(self)`:
  Called by `bt_export_now`.
  Writes an Excel file with the data in tab2
  
# History 
AeffGUI is based on v20 or so of `analy_fluo` which in turn 
is somehow similar to `superpose_ex_situ_images`