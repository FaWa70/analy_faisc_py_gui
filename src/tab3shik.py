def load_stack(self):
    """ Called by:
    Load_File, crop_or_uncrop

    Load all images to memory
    :return:
    """
    print('load_stack called')
    global imStack
    global roiS
    global masked, mask_during_modif
    global im1_width, im1_height  # size of the original images
    global sat_value  # the maximum integer value in the images

    main.statBar.showMessage('Reading images... please wait')
    file_res_info = "Image size (horiz, vert) in pixels: "

    if file_type.upper() == "WCF":  # read wcf file that contains 64 images (taken in identic cond.)
        # get image resolution from filesize
        fi_size = os.path.getsize(f_name)
        print("fi_size = ", fi_size, " Bytes")
        pix_num_est = int(np.round((fi_size - 934 - 5592) / 64 / 2 / 1000))  # kpixels
        #  934 was found by trial and error in comparison to Dataray software
        #  5592 can be read in the first header
        #  64 images
        #  2 bytes per pixel
        print("pix_num_est = ", pix_num_est, " kpixels")
        std_image_reslS = {  # key in in kpixels, tuple in pixels
            int(np.round(64 * 64 / 1000)): (64, 64),
            int(np.round(128 * 128 / 1000)): (128, 128),
            int(np.round(256 * 256 / 1000)): (256, 256),
            int(np.round(348 * 348 / 1000)): (348, 348),
            int(np.round(512 * 512 / 1000)): (512, 512),
            int(np.round(752 * 752 / 1000)): (752, 752),
            int(np.round(1024 * 1024 / 1000)): (1024, 1024),
            int(np.round(1200 * 1024 / 1000)): (1200, 1024)
        }
        try:
            im1_height = std_image_reslS[pix_num_est][1]
            im1_width = std_image_reslS[pix_num_est][0]
            file_res_info = file_res_info + "{:d}, {:d}; uint16".format(im1_width, im1_height)
            self.LbImageSize.setText(file_res_info)
            sat_value = 2 ** 16 - 1

        except KeyError:
            im1_width = np.nan
            im1_height = np.nan
            file_res_info = file_res_info + "NAN, NAN"
            self.LbImageSize.setText(file_res_info)
            sat_value = 10
            return  # exit this function, if image size estimation not successful

        # start loading
        im_size_in_bytes = im1_width * im1_height * 2  # 2 bytes per pixel (uint16)
        main.progBar.setMinimum(0)
        main.progBar.setMaximum(64)
        cm = 1  # pixel (crop margin, because the nominal image size contains a saturated pixel)
        imStack = np.ndarray((im1_height - 2 * cm, im1_width - 2 * cm, 64))  # reserve memory for stack
        with open(f_name, mode="rb") as f:
            f.seek(934 + 5592)
            #  934 was found by trial and error in comparison to Dataray software
            #  5592 can be read in the first header
            im_data = f.read(im_size_in_bytes)
            main.progBar.setValue(1)
            QApplication.processEvents()
            for im_num in range(64):  # 64 images
                # extract the image from the array of bytes and store it (except the outer frame)
                im_data = struct.unpack("H" * ((len(im_data)) // 2), im_data)  # "H" is uint16
                imStack[:, :, im_num] = np.reshape(im_data, (im1_height, im1_width))[cm:-cm, cm:-cm]
                # imStack[:, :, im_num] = np.reshape(im_data, (im1_height, im1_width))

                main.progBar.setValue(im_num + 1)
                QApplication.processEvents()

                # read the next array of bytes
                im_data = f.read(im_size_in_bytes)
        # f.close() is not needed after with block
        im1_height = im1_height - 2 * cm  # for the global variable to reflect the size on imstack
        im1_width = im1_width - 2 * cm
        main.progBar.setValue(0)


    def make_result_dict(self):
        print('make_result_dict called')
        global results  # dict with the results of the current stack defined by good_idx

        # Prepare the variables for the basic calculations results
        # The keys will be used as headers of the Excel sheet and the cobos fpr plotting the histograms
        results = {}  # reset from earlier uses
        res_imno = np.ones(len(good_idx)) * np.nan
        res_aeff = np.ones(len(good_idx)) * np.nan
        res_slope = np.ones(len(good_idx)) * np.nan
        res_straightn = np.ones(len(good_idx)) * np.nan
        res_max = np.ones((len(good_idx), 3)) * np.nan  # takes x, y, z
        res_backg = np.ones(len(good_idx)) * np.nan
        res_energy = np.ones(len(good_idx)) * np.nan

        # Prepare the variables for the fit results
        if ((self.TbFit2.cellWidget(0, 0).currentText() == "Yes") or
                (self.TbFit2.cellWidget(0, 1).currentText() == "Yes") or
                (self.TbFit2.cellWidget(0, 2).currentText() == "Yes")):
            res_b_fit = np.array(len(good_idx) * [[None, None, None]])  # array with dicts as elements

        # build the values (mostly arrays) of the dict
        self.tabs.setCurrentIndex(1)
        main.statBar.showMessage("Analysing stack")
        main.progBar.setMinimum(1)  # if it's not done here, it has to be done at different places later on
        main.progBar.setMaximum(len(good_idx))
        QApplication.processEvents()
        ti_stack_0 = ti.time()
        for idx in range(len(good_idx)):
            self.SlNum2.setValue(idx + 1)  # triggers the calculations using the settings defined on tab2

            res_imno[idx] = good_idx[idx] + 1  # image number in initial stack (wcf-file)
            res_aeff[idx] = Aeffg
            res_slope[idx] = slope
            res_straightn[idx] = np.nan
            res_max[idx] = b_max  # takes x, y, z
            res_backg[idx] = backg
            res_energy[idx] = energy

            if self.TbFit2.cellWidget(0, 0).currentText() == "Yes":  # Round Gauss fit done
                res_b_fit[idx, 0] = b_fits[0][0]
                res_b_fit[idx, 0]["max"] *= b_max[2]  # remove normalization
            if self.TbFit2.cellWidget(0, 1).currentText() == "Yes":  # SOT fit done
                res_b_fit[idx, 1] = b_fits[0][1]
                res_b_fit[idx, 1]["max"] *= b_max[2]  # remove normalization
            if self.TbFit2.cellWidget(0, 2).currentText() == "Yes":  # Elliptic Gauss fit done
                res_b_fit[idx, 2] = b_fits[0][2]
                res_b_fit[idx, 2]["max"] *= b_max[2]  # remove normalization

            main.progBar.setValue(idx + 1)
            QApplication.processEvents()

        # Fill the results-dict using the values above and define the keys at the same time
        # The keys will be used as headers of the Excel sheet and the cobos fpr plotting the histograms
        results["Image number"] = res_imno
        results["Effective surface (px²)"] = res_aeff
        results["Aeff slope"] = res_slope
        results["Aeff straightness"] = res_straightn
        results["Max value (GL)"] = res_max[:, 2]
        results["Background (GL)"] = res_backg
        results["Energy (GL)"] = res_energy
        results["Max pos X (px)"] = res_max[:, 0]
        results["Max pos Y (px)"] = res_max[:, 1]
        # "status" "GOF" "w1" "max" "x_0" "y_0" "w2" "angle" (useful entries of fit parameter dicts)
        if self.TbFit2.cellWidget(0, 0).currentText() == "Yes":  # Round Gauss fit done
            results["RG beam radius w1 (px)"] = np.array([res_b_fit[row, 0]["w1"] for row in range(len(good_idx))])
            results["RG Max value (GL)"] = np.array([res_b_fit[row, 0]["max"] for row in range(len(good_idx))])
            results["RG Max pos X (px)"] = np.array([res_b_fit[row, 0]["x_0"] for row in range(len(good_idx))])
            results["RG Max pos Y (px)"] = np.array([res_b_fit[row, 0]["y_0"] for row in range(len(good_idx))])
            results["RG status"] = list([res_b_fit[row, 0]["status"] for row in range(len(good_idx))])
            results["RG GOF"] = np.array([res_b_fit[row, 0]["GOF"] for row in range(len(good_idx))])
        if self.TbFit2.cellWidget(0, 1).currentText() == "Yes":  # SOT fit done
            results["Gsot beam radius w1 (px)"] = np.array([res_b_fit[row, 1]["w1"] for row in range(len(good_idx))])
            results["Gsot Max value (GL)"] = np.array([res_b_fit[row, 1]["max"] for row in range(len(good_idx))])
            results["Gsot status"] = list([res_b_fit[row, 1]["status"] for row in range(len(good_idx))])
            results["Gsot GOF"] = np.array([res_b_fit[row, 1]["GOF"] for row in range(len(good_idx))])
        if self.TbFit2.cellWidget(0, 2).currentText() == "Yes":  # Elliptic Gauss fit done
            results["EllG beam radius w1 (px)"] = np.array([res_b_fit[row, 2]["w1"] for row in range(len(good_idx))])
            results["EllG beam radius w2 (px)"] = np.array([res_b_fit[row, 2]["w1"] for row in range(len(good_idx))])
            results["EllG long axis angle (°)"] = np.array([res_b_fit[row, 2]["angle"] for row in range(len(good_idx))])
            results["EllG Max value (GL)"] = np.array([res_b_fit[row, 2]["max"] for row in range(len(good_idx))])
            results["EllG Max pos X (px)"] = np.array([res_b_fit[row, 2]["x_0"] for row in range(len(good_idx))])
            results["EllG Max pos Y (px)"] = np.array([res_b_fit[row, 2]["y_0"] for row in range(len(good_idx))])
            results["EllG status"] = list([res_b_fit[row, 2]["status"] for row in range(len(good_idx))])
            results["EllG GOF"] = np.array([res_b_fit[row, 2]["GOF"] for row in range(len(good_idx))])
        # probably there is a better way to do this

        # populate combo boxes for display of histograms and x-y-scatter
        CobPl_li = [self.CobPl31, self.CobPl32, self.CobPl33, self.CobPl34]
        key_li = list(results.keys())
        print("key_li = ", key_li)
        for this_cobo_num, this_cobo in enumerate(CobPl_li):
            this_cobo.clear()
            this_cobo.addItems(list(results.keys()))
            this_cobo.setCurrentIndex(this_cobo_num + 1)

        self.show_res_statistics_table(ti_stack_0)