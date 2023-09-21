"""
Models and helper functions for fits
Demo functions too
"""
from time import time as tic
import numpy as np
import matplotlib.pyplot as plt
import scipy.optimize as opt

plt.close("all")
np.set_printoptions(suppress=True, precision=3)

"""Helper functions"""


def simul_data(model, paras, rel_noise=0.05, x_mi=-2, x_ma=4, num=250):
    """Generate noisy data to start with"""
    x_vals = np.linspace(x_mi, x_ma, num=num)
    y_vals = model.f(x_vals, paras)
    y_vals = y_vals * (1 + np.random.default_rng().normal(0, rel_noise, len(x_vals)))
    # print("test data for nans:", np.any(np.isnan(y_vals)))
    return x_vals, y_vals


def simul_2D_data(model, paras, rel_noise=0.05, x_mi=-2, x_ma=4, num=250):
    """Generate noisy data to start with"""
    x_vals = np.linspace(x_mi, x_ma, num=num)
    y_vals = x_vals  # square support region
    z_vals = model.f(x_vals, y_vals, paras)
    z_vals = z_vals * (1 + np.random.default_rng().normal(0, rel_noise, len(x_vals)))
    # print("test data for nans:", np.any(np.isnan(y_vals)))
    return x_vals, y_vals, z_vals


def goodness_of_fit(mes_x, mes_y, model, parameters):
    """ Goodness of fit evaluation:
    mes_x: x-data of the measurements
    mes_y: y-data of the measurements (same length as mes_x)
    model: a function name with two arguments (x-values, parameter_vector)
    parameters: a parameter vector accepted by the model

    This mostly follows the Spiess and Neumeyer publication from 2010
    It supposes normal statistics. (Not ok for probability measurements)

    They say that AICc is better than r_squ_c and that BIC has a higher penalty
    on useless parameters (fitting a Gaussian on an exponential decay...)

    return AICc, r_squ_c, BIC, r_squ, AIC
    """
    # TODO : Perhaps implement an evaluation by extrapolation capacities:
    # The idea: A fit interpolates the data. For Gaussian data (depending on the x range)
    # a poly12 fit can do this nearly as good as a Gaussian model (though with much more parameters).
    # However, the number of used parameters only has little influence in the goodness_of_fit (GOF)
    # parameters (even BIC only moves slowly with over parametrization).
    # The idea is that one could fit the 80-90% of the data on the left side and then check how well the
    # unused 5-10% of the data on the right side are described by the model.
    # If it's the real model this should be rather close to the corrected GOF parameters of the fitted part

    if not isinstance(mes_x, np.ndarray):
        mes_x = np.array(mes_x)
    if not isinstance(mes_y, np.ndarray):
        mes_y = np.array(mes_y)

    # rsquared
    ss_res = model.chi2(parameters, mes_x, mes_y)  # I used : chi² = sum of squared residuals
    ss_tot = ((mes_y - mes_y.mean()) ** 2).sum()
    r_squ = 1 - (ss_res / ss_tot)

    # rsquared corrected for different degrees of freedom (absolute value but insensitive)
    num_mes = len(mes_x)
    num_par = len(parameters)
    r_squ_c = 1 - (num_mes - 1) / (num_mes - num_par) * (1 - r_squ)

    # Akaike Information Criterion: AIC (good for model comparisons, relative value)
    log_likelyhood = -num_mes / 2 * (np.log(2 * np.pi * ss_res / num_mes) + 1)
    AIC = 2 * (num_par + model.negated_log_likelihood(parameters, mes_x, mes_y))

    # AIC corrected for different degrees of freedom
    AICc = AIC + (2 * num_par * (num_par + 1)) / (num_mes - num_par - 1)

    # Bayesian Information Criterion: BIC (higher penalty on nb of params)
    BIC = num_par * np.log(num_mes) + 2 * model.negated_log_likelihood(parameters, mes_x, mes_y)

    return AICc, r_squ_c, BIC, r_squ, AIC


"""Demonstration functions that compare fits with different models:
Fit the models from fit_model_list to the data:

Do not give uncertainties for the data, but expect uncertainties for the parameters
... compare speed of leastsq and curve_fit
... see if corrected R² or corrected AIC points out the right model

If the uncertainties of the parameters are not needed (e.g. for bootstrapping) 
use leastsq, it's faster! 
"""


def using_leastsq(x_vals, y_vals, fit_model_list):
    """fit_model_list: the list of models to compare in terms of
    the output of goodness_of_fit"""
    print("\n---------using_leastsq------------------------")
    # make the plot
    plt.figure()
    plt.title("Different models on " + type(simul_model).__name__ + " data - leastsq")
    plt.plot(x_vals, y_vals, '.')

    # prepare goodness_of_fit comparison
    goodness_x = []
    goodness_model_names = []
    goodness_AICc = []
    goodness_r_sq_c = []
    goodness_BIC = []
    average_time = []

    # Fit it
    for mod_no, model in enumerate(fit_model_list):
        print("\n-- fitted by ----", type(model).__name__)

        # complete (with uncertainty information and error message)
        pfit, pcov, _, errmsg, success = \
            opt.leastsq(model.residuals, model.guess(x_vals, y_vals),  # calls model.residuals(paras0, x_vals, y_vals)
                        args=(x_vals, y_vals), full_output=True, epsfcn=0.0001)
        if success not in [1, 2, 3, 4]:  # If success is equal to 1, 2, 3 or 4, the solution was found.
            print(errmsg)

        # Simple (no uncertainty information) : remove parameter uncertainty block below
        # This simple call accelerates the execution (bootstrapping)
        # pfit, success = opt.leastsq(model.residuals, model.guess(x_vals, y_vals),
        #                          args=(x_vals, y_vals), full_output=False, epsfcn=0.0001)
        # if success not in [1, 2, 3, 4]:  # If success is equal to 1, 2, 3 or 4, the solution was found.
        #     print("Fitting problem encountered")

        # just for measuring execution time if wanted
        max_runs = 100
        t1 = tic()
        for runs in range(max_runs):
            _, _, _, _, _ = opt.leastsq(model.residuals, model.guess(x_vals, y_vals),
                                        args=(x_vals, y_vals), full_output=True, epsfcn=0.0001)
        delta_t = (tic() - t1) / max_runs
        print("This took", delta_t, "seconds in average.")

        # calculate parameter uncertainties from pcov output
        if (len(y_vals) > len(pfit)) and pcov is not None:
            pcov = pcov * model.chi2(pfit, x_vals, y_vals) / (len(y_vals) - len(pfit))
            # cov_x (ndarray) : The inverse of the Hessian. A value of None indicates a singular matrix,
            # which means the curvature in parameters x is numerically flat.
            # To obtain the covariance matrix of the parameters x, cov_x must be multiplied
            # by the variance of the residuals – see curve_fit.
        else:
            pcov = np.inf
        uncertainties = []
        for i in range(len(pfit)):
            try:
                uncertainties.append(np.abs(pcov[i][i]) ** 0.5)
            except:
                uncertainties.append(0.00)

        # Generate GoF indices
        AICc, r_squ_c, BIC, _, _ = goodness_of_fit(x_vals, y_vals, model, pfit)

        # Output
        print("Best params: ", np.array(pfit))
        print("Uncertainties: ", np.array(uncertainties))
        print("Rel. uncert.: ", np.array(uncertainties / pfit))
        print("AICc1 =", AICc)
        print("r_squ_c1 =", r_squ_c)
        print("BIC =", BIC)

        plt.plot(x_vals, model.f(x_vals, pfit),
                 label=(type(model).__name__ +
                        ": AICc:" + np.format_float_scientific(AICc, exp_digits=1, precision=2) +
                        "; r_squ_c:{:3.2}".format(r_squ_c) +
                        "; BIC:" + np.format_float_scientific(BIC, exp_digits=1, precision=2)))

        goodness_x.append(mod_no)
        goodness_model_names.append(type(model).__name__)
        goodness_AICc.append(AICc)
        goodness_r_sq_c.append(r_squ_c)
        goodness_BIC.append(BIC)
        average_time.append(delta_t)

    plt.ylim(y_vals.min() - abs(0.1 * y_vals.min()),
             y_vals.max() + abs(0.05 * y_vals.max()))
    plt.legend()  # no longer necessary, as now the second plot shows the goodness of fit values

    fig, ax1 = plt.subplots()
    plt.title("Different models on " + type(simul_model).__name__ + " data - leastsq")
    goodness_x = np.array(goodness_x)
    bar_width = 1 / 5
    rects1 = ax1.bar(goodness_x - bar_width, goodness_AICc, 0.2)
    rects3 = ax1.bar(goodness_x + bar_width, goodness_BIC, 0.2)
    ax1.set_xticks(goodness_x)
    ax1.set_xticklabels(goodness_model_names)
    ax1.set_ylabel('AICc and BIC')

    ax2 = ax1.twinx()
    goodness_r_sq_c = np.array(goodness_r_sq_c)
    rects2 = ax2.bar(goodness_x, 1 - goodness_r_sq_c, 0.2, color='g', )
    ax2.set_ylabel('1 - r_sq_c')

    ax2.legend((rects1[0], rects2[0], rects3[0]), ('AICc', '1 - r_sq_c', 'BIC'))
    return average_time


def using_boot_leastsq(x_vals, y_vals, fit_model_list):
    """fit_model_list: the list of models to compare in terms of
    the output of goodness_of_fit"""
    print("\n---------using leastsq in a bootstrap without data uncertainty -------------------")
    print("(Just check that we can reproduce the uncertainty due to the data dispersion by bootstrapping.)")
    # Don't make the plots for this one just compare the text output

    # prepare goodness_of_fit comparison
    average_time = []

    # Fit it
    for model in fit_model_list:
        print("\n-- fitted by ----", type(model).__name__)

        # First call with precise but scattered data points (simple and fast call)
        pfit, success = opt.leastsq(model.residuals, model.guess(x_vals, y_vals),
                                    args=(x_vals, y_vals), full_output=False, epsfcn=0.0001)
        if success not in [1, 2, 3, 4]:  # If success is equal to 1, 2, 3 or 4, the solution was found.
            print("  !! Fitting problem encountered")

        # Get the stdev of the residuals of first fit (this is due to data scatter,
        # not to the uncertainties of each data point)
        sigma_res = np.std(model.residuals(pfit, x_vals, y_vals))

        # If you know the uncertainty of each data point, add them using this formula
        y_vals_uncertainty = np.zeros(y_vals.shape)
        sigma_err_total = np.sqrt(sigma_res ** 2 + y_vals_uncertainty ** 2)

        # Many random data sets are simulated and fitted
        max_runs = 500
        fit_parameter_collection = []
        t1 = tic()
        for i in range(max_runs):
            delta_y = np.random.normal(0., sigma_err_total, len(y_vals))
            y_vals_simul = y_vals + delta_y

            # (simple and fast call)
            pfit_simul, success = opt.leastsq(model.residuals, model.guess(x_vals, y_vals_simul),
                                              args=(x_vals, y_vals_simul), full_output=False, epsfcn=0.0001)

            fit_parameter_collection.append(pfit_simul)  # possibly put this in an - if success:
        delta_t = (tic() - t1) / max_runs
        print("This took", delta_t, "seconds in average. (", max_runs, "samples)")

        # The statistics of the fit parameters give value (mean) and uncertainty of the best parameters
        fit_parameter_collection = np.array(fit_parameter_collection)
        pfit = np.mean(fit_parameter_collection, 0)
        uncertainties = 1 * np.std(fit_parameter_collection, 0)  # A factor 1 corresponds to 68.3% confidence

        # Generate GoF indices
        AICc, r_squ_c, BIC, _, _ = goodness_of_fit(x_vals, y_vals, model, pfit)

        # Output
        print("Best params: ", np.array(pfit))
        print("Uncertainties: ", np.array(uncertainties))
        print("Rel. uncert.: ", np.array(uncertainties / pfit))
        print("AICc1 =", AICc)
        print("r_squ_c1 =", r_squ_c)
        print("BIC =", BIC)

        average_time.append(delta_t)
    return average_time

def print_strong_corrs(pcorr, maxcnum=-10, corr_limit=0.6):
    """Prints the maxcnum strongest correlated parameter pairs.
    If there is one higher than +/- 0.75, think about eliminating a parameter from the model
    corr_limit is stronger than maxcnum.
    """
    corrs = np.triu(pcorr, k=1).flatten()  # extract the upper triangular part avoiding the main diagonal
    corrs_abs = np.abs(corrs)
    idx_both = np.triu_indices_from(pcorr, k=1)
    idx_1 = idx_both[0].flatten()
    idx_2 = idx_both[1].flatten()

    nz = np.nonzero(corrs_abs)  # remove the zero entries created by np.triu
    corrs_abs = corrs_abs[nz].copy()
    corrs = corrs[nz].copy()

    order = np.argsort(corrs_abs)[::-1]
    corrs = corrs[order].copy()
    idx_1 = idx_1[order].copy()
    idx_2 = idx_2[order].copy()

    if (maxcnum == -10) or (maxcnum > len(corrs)):
        maxcnum = len(corrs)

    if (corrs_abs > corr_limit).sum() < maxcnum:
        maxcnum = (corrs_abs > corr_limit).sum()
    if maxcnum == 0:
        print(f"No correlations of more than {corr_limit:.3f} found. \n" +
              f"(add option corr_limit=x.xx to change the limit)")

    for comb in range(maxcnum):
        print(f"Corr. of {corrs[comb]:.3f} between parameter {idx_1[comb]:d} and {idx_2[comb]:d}")

def curve_fit_errs_and_corrs(pcov, print_unc=True, print_p_corrs=True, corr_limit=0.6,
                             return_unc=False, return_pcorrs=False):
    """
    Print or get as return the fit parameter uncertainties and their correlation coefficients.
    If the correlation coefficient is 1, the two parameters have the same physical meaning.
    :param pcov: Output from scipy.optimize.curve_fit
    :param print_unc: True: The results are shown on the console
    :param print_p_corrs: True: The results are shown on the console
    :param return_unc: True: Return the array of absolute uncertainties as first output of this fct.
    :param return_pcorrs: True: Return the correlation matrix as second output
    :return:
    """
    # get parameter uncertainties
    unc = []
    for i in range(len(pcov)):
        try:
            unc.append(np.absolute(pcov[i][i]) ** 0.5)
        except:
            unc.append(-10.0)  # nonsense: indicates run time error
    unc = np.array(unc)
    if print_unc:
        print("Uncertainties: ", unc)
    # see if there are dependent parameters (correlation matrix)
    he = np.diag(1 / unc)  # helper matrix
    pcorr = he @ pcov @ he  # use helper function print_strong_corrs(pcorr, ...) for output
    if print_p_corrs:
        print_strong_corrs(pcorr, maxcnum=-10, corr_limit=corr_limit)
    if return_unc and not return_pcorrs:
        return unc
    elif return_unc and return_pcorrs:
        return unc, pcorr
    else:
        return


def using_curve_fit(x_vals, y_vals, fit_model_list):
    """paras1: the REAL parameters for simul_model: pre_factor, exp_factor, offset
    fit_model_list: the list of models to compare in terms of corrected R² or AICc"""
    print("\n---------using_curve_fit------------------------")
    # make the plot
    plt.figure()
    plt.title("Different models on " + type(simul_model).__name__ + " data - curve-fit")
    plt.plot(x_vals, y_vals, '.')

    # prepare goodness_of_fit comparison
    goodness_x = []
    goodness_model_names = []
    goodness_AICc = []
    goodness_r_sq_c = []
    goodness_BIC = []
    average_time = []

    # Fit it
    for mod_no, model in enumerate(fit_model_list):
        print("\n-- fitted by ----", type(model).__name__)

        pfit, pcov = opt.curve_fit(model.f_sep, x_vals, y_vals,
                                   p0=model.guess(x_vals, y_vals), epsfcn=0.0001)

        # just for measuring execution time if wanted
        max_runs = 100
        t1 = tic()
        for runs in range(max_runs):
            _, _ = opt.curve_fit(model.f_sep, x_vals, y_vals,
                                 p0=model.guess(x_vals, y_vals), epsfcn=0.0001)
        delta_t = (tic() - t1) / max_runs
        print("This took", delta_t, "seconds in average.")

        # get parameter uncertainties
        uncertainties = []
        for i in range(len(pfit)):
            try:
                uncertainties.append(np.absolute(pcov[i][i]) ** 0.5)
            except:
                uncertainties.append(0.0)
        uncertainties = np.array(uncertainties)

        # see if there are dependent parameters (correlation matrix)
        he = np.diag(1/uncertainties)  # helper matrix
        pcorr = he @ pcov @ he  # use helper function print_strong_corrs(pcorr, ...) for output

        # Generate GoF indices
        AICc, r_squ_c, BIC, _, _ = goodness_of_fit(x_vals, y_vals, model, pfit)

        # Output
        print("Best params: ", np.array(pfit))
        print("Uncertainties: ", np.array(uncertainties))
        print("Rel. uncert.: ", np.array(uncertainties / pfit))
        print("AICc1 =", AICc)
        print("r_squ_c1 =", r_squ_c)
        print("BIC =", BIC)
        print_strong_corrs(pcorr)

        plt.plot(x_vals, model.f(x_vals, pfit),
                 label=(type(model).__name__ +
                        ": AICc:" + np.format_float_scientific(AICc, exp_digits=1, precision=2) +
                        "; r_squ_c:{:3.2}".format(r_squ_c) +
                        "; BIC:" + np.format_float_scientific(BIC, exp_digits=1, precision=2)))

        goodness_x.append(mod_no)
        goodness_model_names.append(type(model).__name__)
        goodness_AICc.append(AICc)
        goodness_r_sq_c.append(r_squ_c)
        goodness_BIC.append(BIC)
        average_time.append(delta_t)

    plt.ylim(y_vals.min() - abs(0.1 * y_vals.min()),
             y_vals.max() + abs(0.05 * y_vals.max()))
    plt.legend()  # no longer necessary, as now the second plot shows the goodness of fit values

    fig, ax1 = plt.subplots()
    plt.title("Different models on " + type(simul_model).__name__ + " data - curve-fit")
    goodness_x = np.array(goodness_x)
    bar_width = 1 / 5
    rects1 = ax1.bar(goodness_x - bar_width, goodness_AICc, 0.2)
    rects3 = ax1.bar(goodness_x + bar_width, goodness_BIC, 0.2)
    ax1.set_xticks(goodness_x)
    ax1.set_xticklabels(goodness_model_names)
    ax1.set_ylabel('AICc and BIC')

    ax2 = ax1.twinx()
    goodness_r_sq_c = np.array(goodness_r_sq_c)
    rects2 = ax2.bar(goodness_x, 1 - goodness_r_sq_c, 0.2, color='g', )
    ax2.set_ylabel('1 - r_sq_c')

    ax2.legend((rects1[0], rects2[0], rects3[0]), ('AICc', '1 - r_sq_c', 'BIC'))
    return average_time


def using_minimize(x_vals, y_vals, fit_model_list):
    """paras1: the REAL parameters for simul_model: pre_factor, exp_factor, offset
    fit_model_list: the list of models to compare in terms of corrected R² or AICc"""
    print("\n---------using_minimize------------------------")
    # make the plot
    plt.figure()
    plt.title("Different models on " + type(simul_model).__name__ + " data - minimize")
    plt.plot(x_vals, y_vals, '.')

    # prepare goodness_of_fit comparison
    goodness_x = []
    goodness_model_names = []
    goodness_AICc = []
    goodness_r_sq_c = []
    goodness_BIC = []
    average_time = []

    # Fit it
    for mod_no, model in enumerate(fit_model_list):
        print("\n-- fitted by ----", type(model).__name__)

        ftol = 1e-4  # fit stop criterion also used for uncertainty calculation (normal distributed)
        pfit = opt.minimize(model.cost, model.guess(x_vals, y_vals), args=(x_vals, y_vals), tol=ftol)
        # pfit = opt.minimize(model.cost, model.guess(x_vals, y_vals), args=(x_vals, y_vals))
        # with or without tol=ftol=1e-4 the AICc is slightly higher.

        # print("pfit = \n", pfit)
        if not pfit.success:  # Here success is True or False
            print("!!", pfit.message)

        # get parameter uncertainties - Does not seem to be possible in the general case
        # should be similar to leastsq BUT makes problems
        # uncertainties = np.zeros(len(pfit.x))
        # correction_factor = model.chi2(pfit.x, x_vals, y_vals) / (len(y_vals) - len(pfit.x))  # like for leastsq
        # tmp_i = np.zeros(len(pfit.x))
        # for i in range(len(pfit.x)):
        #     tmp_i[i] = 1.0  # tmp_i is the vector [0 ,..,0 ,1 ,0 ,..0]
        #     if isinstance(pfit.hess_inv, np.ndarray):  # this may be np.ndarray or ..
        #         hess_inv_i = (pfit.hess_inv @ tmp_i)[i]  # matrix multiplication (better (newer) than dot)
        #     else:
        #         hess_inv_i = pfit.hess_inv(tmp_i)[i]  # this may be .. or scipy.sparse.linalg.LinearOperator
        #     # print(hess_inv_i)
        #     uncertainties[i] = np.sqrt(np.abs(hess_inv_i * correction_factor))
        #     tmp_i[i] = 0.0

        pfit = pfit.x  # just keep the best parameters of the return object

        # just for measuring execution time if wanted
        max_runs = 100
        t1 = tic()
        for runs in range(max_runs):
            # _ = opt.minimize(model.cost, model.guess(x_vals, y_vals), args=(x_vals, y_vals))
            _ = opt.minimize(model.cost, model.guess(x_vals, y_vals), args=(x_vals, y_vals), tol=0.0001)
        delta_t = (tic() - t1) / max_runs
        print("This took", delta_t, "seconds in average.")

        # Generate GoF indices
        AICc, r_squ_c, BIC, _, _ = goodness_of_fit(x_vals, y_vals, model, pfit)

        # Output
        print("Best params: ", np.array(pfit))
        # print("Uncertainties: ", np.array(uncertainties))
        # print("Rel. uncert.: ", np.array(uncertainties / pfit))
        print("Uncertainties NOT OK")
        print("AICc1 =", AICc)
        print("r_squ_c1 =", r_squ_c)
        print("BIC =", BIC)

        plt.plot(x_vals, model.f(x_vals, pfit),
                 label=(type(model).__name__ +
                        ": AICc:" + np.format_float_scientific(AICc, exp_digits=1, precision=2) +
                        "; r_squ_c:{:3.2}".format(r_squ_c) +
                        "; BIC:" + np.format_float_scientific(BIC, exp_digits=1, precision=2)))

        goodness_x.append(mod_no)
        goodness_model_names.append(type(model).__name__)
        goodness_AICc.append(AICc)
        goodness_r_sq_c.append(r_squ_c)
        goodness_BIC.append(BIC)
        average_time.append(delta_t)

    plt.ylim(y_vals.min() - abs(0.1 * y_vals.min()),
             y_vals.max() + abs(0.05 * y_vals.max()))
    plt.legend()  # no longer necessary, as now the second plot shows the goodness of fit values

    fig, ax1 = plt.subplots()
    plt.title("Different models on " + type(simul_model).__name__ + " data - minimize")
    goodness_x = np.array(goodness_x)
    bar_width = 1 / 5
    rects1 = ax1.bar(goodness_x - bar_width, goodness_AICc, 0.2)
    rects3 = ax1.bar(goodness_x + bar_width, goodness_BIC, 0.2)
    ax1.set_xticks(goodness_x)
    ax1.set_xticklabels(goodness_model_names)
    ax1.set_ylabel('AICc and BIC')

    ax2 = ax1.twinx()
    goodness_r_sq_c = np.array(goodness_r_sq_c)
    rects2 = ax2.bar(goodness_x, 1 - goodness_r_sq_c, 0.2, color='g', )
    ax2.set_ylabel('1 - r_sq_c')

    ax2.legend((rects1[0], rects2[0], rects3[0]), ('AICc', '1 - r_sq_c', 'BIC'))
    return average_time


def leastsq_1by1_fit(model, paras0, x, y):
    """unbound fitting but one parameter at the time to reach a physical meaningful
    local minimum of chi2
    model is a function that takes (x-values, parameters)
    The parameters are fitted in the order they are listed.
    """

    def resid_for_1par_fit(fit_p, fit_p_idx, other_ps, mod, x_vals, y_vals):
        """returns the signed residual for fitting a single parameter fit_p
        at position fit_p_idx in the mod parameters"""
        if len(other_ps) + 1 != len(paras0):
            print("resid_for_1par_fit: wrong number of parameters")
            return
        call_ps = np.zeros(len(other_ps) + 1)
        call_ps[:fit_p_idx] = other_ps[:fit_p_idx]
        call_ps[fit_p_idx] = fit_p
        call_ps[fit_p_idx + 1:] = other_ps[fit_p_idx:]
        # print(call_ps)
        return mod(x_vals, call_ps) - y_vals

    if not isinstance(paras0, np.ndarray):
        paras0 = np.array(paras0)
    best_ps = paras0.copy()
    for fit_par_idx in range(len(paras0)):
        other_pars = best_ps[np.arange(len(best_ps)) != fit_par_idx]
        pfit, success = opt.leastsq(resid_for_1par_fit, paras0[fit_par_idx],
                                    args=(fit_par_idx, other_pars, model, x, y), full_output=False, epsfcn=0.0001)
        if success not in [1, 2, 3, 4]:  # If success is equal to 1, 2, 3 or 4, the solution was found.
            print("Fitting problem encountered")
        best_ps[fit_par_idx] = pfit
    return best_ps


"""Demonstration function that fits data with uncertainties ...
It seems that only bootstrapping gives reasonable parameter uncertainties
even though curve_fit should do it too. 
"""
# TODO: Give example of bootstrapping function


"""Models to test"""


class FitModel:
    """The purpose is to provide the model function (equation), model.f,
    and the guess of the best initial parameters, model.guess, for every specific model
    by analysing the measurement data.
    For these two methods only a template for the arguments is implemented here

    There are also helper functions evaluating the local scatter and for smoothing
    the data before making the guess.

    Finally I also put here functions that are needed by the fitting routines:
    model.residuals -> scipy.optimize.leastsq(model.residuals, ...)
        scipy.optimize.leastsq(model.residuals, paras0, args=(x_vals_1, y_vals_1))
        # calls model.residuals(paras0, x_vals_1, y_vals_1)
    (scipy.optimize.curve_fit uses model.f:
        scipy.optimize.curve_fit(model.f, data_x, data_y, p0=[2,2,1,1])    )
    Define cost function to minimize ( chi² or -Log(likelihood) )
        def cost(paras_opt, data_x, data_y):
        scipy.optimize.minimize(cost, x0=(2,2), args=(data_x,data_y) )
    """

    # Or more generally a cost function, which can be chi² or -log(likelihood) or
    # something else like horizontality for the line-fit on the last points in the
    # software aperture method for background subtraction.

    def f(self, x_values, paras):  # uses a single parameter vector
        print("No formula defined")
        return

    def guess(self, x_values, y_values):
        print("Guess of initial parameters not implemented")
        return

    def f_sep(self, x_values, *paras):  # uses many separate parameters
        """Helper function for fits with optimize.curve_fit"""
        return self.f(x_values, np.array(paras))
        # If not all params in model shall be fitted see at the en dof this file

    def residuals(self, p, x, y):
        """Helper function for fits with optimize.leastsq and self.chi2"""
        diff = self.f(x, p) - y  # difference with sign
        # If not all params in model shall be fitted define a new version of residuals
        return diff

    def resid_2D(self, p, x, y, z, **kwargs):
        """Helper function for fits with optimize.leastsq and self.chi2"""
        diff = self.f(x, y, p, **kwargs) - z  # difference with sign
        # If not all params in model shall be fitted define a new version of residuals
        return diff.ravel()  # leastsq expects 1D data from any model

    def chi2(self, p, x, y):
        """chi2(self, p, x, y) = residuals(p, x, y)**2).sum()
        where residuals(p, x, y) = f(x, p) - y_data"""
        return (self.residuals(p, x, y) ** 2).sum()

    def negated_log_likelihood(self, p, x, y):
        """negated_log_likelihood is often the thing to minimize.
        It's also a helper function for goodness_of_fit.
        Depends on the data statistics. As standard the -log(L) for
        normally distributed data is implemented here (publication by Spiess
        and Neumeyer)"""
        ss_res = self.chi2(p, x, y)  # I used : chi² = sum of squared residuals
        return len(x) / 2 * (np.log(2 * np.pi * ss_res / len(x)) + 1)

    def cost(self, p, x, y):
        """the function to be minimized by optimize.minimize. Usually either
        negated_log_likelihood, or chi2. Was separated to able to be overloaded.
        (For example with slope of fit in software aperture method for offset correction.)"""
        return self.negated_log_likelihood(p, x, y)

    def moving_average(self, x, y, box_pts):
        """moving average, use odd nb of box_pts.
        Is used by guess method"""
        y_smooth = np.cumsum(y, dtype=float)
        y_smooth[box_pts:] = y_smooth[box_pts:] - y_smooth[:-box_pts]
        return x[box_pts // 2:-(box_pts // 2)], y_smooth[box_pts - 1:] / box_pts

    def rel_dev(self, y, pts_from_border):
        """determine the minimum relative deviation between neighboring points
        in the middle and the two extremities of the data.
        Is used by guess method"""
        value_1 = abs(y[pts_from_border - 1] - y[pts_from_border]) / y[pts_from_border]
        value_2 = abs(y[-pts_from_border - 1] - y[-pts_from_border]) / y[-pts_from_border]
        value_3 = abs(y[len(y) // 2 - 1] - y[len(y) // 2]) / y[len(y) // 2]
        return min([value_1, value_2, value_3])


class Gauss_w_z_evol(FitModel):
    """
    Gives the way how the waist evolves with propagation. (The caustic)
    z0: position of the waist
    M2: beam quality
    la0: vacuum wavelength
    w0: smallest waist
    """
    def f(self, z_values, paras):  # M2 has to be 1 or larger
        if not isinstance(z_values, np.ndarray):
            z_values = np.array(z_values)

        z0 = paras[0]
        M2 = paras[1]
        la0 = paras[2]
        w0 = paras[3]
        w_values = w0 * np.sqrt(1 + ((z_values - z0) / (
                                      np.pi * w0**2 / (la0*M2) ))**2)
        return w_values

gauss_w_z_evol = Gauss_w_z_evol()


class SOT_round_gau(FitModel):
    """ Suface over threshold (sot) for a round Gaussian with peak fluence peak_flu and waist w (these are the
    two parameters). No offset is allowed for the Gaussian """

    def f(self, x_values, paras):  # x_values and peak_flu have to be positive
        if not isinstance(x_values, np.ndarray):
            x_values = np.array(x_values)

        peak_flu = paras[0]
        w = paras[1]
        y_values = np.zeros(x_values.shape)
        y_values[x_values < peak_flu] = np.pi * w**2 / 2 * np.log(peak_flu / x_values[x_values < peak_flu])
        return y_values

    def guess(self, x_values, y_values):
        """ maybe later a real function:
        Guess the flu_max from where the increase starts. highest index with y > average of highest 5 vals +
        3 * stddev
        Guess w ... no idea
        But here just manual return
        """
        return np.array([21, 5])

sot_r_gau = SOT_round_gau()


class Gauss1D(FitModel):
    """1D Gaussian with
    y_values = vert_factor * np.exp(-2 * ((x_values - x_shift) / waist_radius) ** 2) + offset"""

    def f(self, x_values, paras):
        """offset is the last in paras"""
        if not isinstance(x_values, np.ndarray):
            x_values = np.array(x_values)

        vert_factor = paras[0]
        x_shift = paras[1]
        waist_radius = paras[2]
        offset = paras[3]
        y_values = vert_factor * np.exp(-2 * ((x_values - x_shift) / waist_radius) ** 2) + offset
        return y_values

    def guess(self, x_values, y_values):
        """for 'bumps' only
            offset is the last in paras
            y_values = vert_factor * np.exp(-2 * ((x_values - x_shift)/waist_radius)**2) + offset
            initial_parameters = [vert_factor, x_shift, waist_radius, offset]
            """
        if not isinstance(x_values, np.ndarray):
            x_values = np.array(x_values)
        if not isinstance(y_values, np.ndarray):
            y_values = np.array(y_values)

        # increase moving average box until min rel variation < rel_dev_lim
        # Stop smoothing if at any position (left, middle, right) the curve is 'horizontal' within rel_dev_lim
        rel_dev_lim = 0.001  # 0.1%
        box_pts_max = len(y_values) // 11  # keep at least 11 independent intervals
        if box_pts_max % 2 != 0:
            box_pts_max += 1  # make it even (and larger)
        box_pts = 1  # start with box of 3 points
        rel_d = self.rel_dev(y_values, box_pts)  # get minimum relative deviation of original data
        y_values_backup = y_values.copy()
        x_values_backup = x_values.copy()
        while (box_pts < box_pts_max) and (rel_d > rel_dev_lim):
            box_pts += 2  # stay with odd numbers
            x_values, y_values = self.moving_average(x_values_backup, y_values_backup, box_pts)
            rel_d = self.rel_dev(y_values, box_pts)

        # y_values = vert_factor * np.exp(-2 * ((x_values - x_shift)/waist_radius)**2) + offset
        # set the easy to guess initial parameters
        offset = y_values.min()
        vert_factor = y_values.max() - offset
        x_shift = x_values[y_values.argmax()]

        # estimate 1/e2 waist radius: find the position(s) where 2 successive points are below the limit
        dec_lim = np.exp(-2)
        waist_idx = round(len(y_values) / 4)  # default value
        max_idx = y_values.argmax()
        diff_r = 0
        while ((max_idx + diff_r + 1 < len(y_values) - 2) and
               (((y_values[max_idx + diff_r] - offset) / vert_factor > dec_lim) or
                ((y_values[max_idx + diff_r + 1] - offset) / vert_factor > dec_lim))):
            diff_r += 1
        diff_g = 0
        while ((max_idx - diff_g - 1 > 0) and
               (((y_values[max_idx - diff_g] - offset) / vert_factor > dec_lim) or
                ((y_values[max_idx - diff_g - 1] - offset) / vert_factor > dec_lim))):
            diff_g += 1
        if (max_idx - diff_g - 1 > 0) and (max_idx + diff_r + 1 < len(y_values) - 2):
            waist_idx = round((diff_g + diff_r) / 2)
        else:
            if max_idx - diff_g - 1 > 0:
                waist_idx = diff_g
            if max_idx + diff_r + 1 < len(y_values) - 2:
                waist_idx = diff_r
        waist_radius = x_values[waist_idx] - x_values[0]

        initial_parameters = [vert_factor, x_shift, waist_radius, offset]
        return initial_parameters


gauss1D = Gauss1D()


class Gauss2D(FitModel):
    """2D Gaussian with
    y_values = vert_factor *
      np.exp(-2 * ((x_values - x_shift) ** 2 + (y_values - y_shift) ** 2) / waist_radius ** 2 ) + offset"""

    def f(self, x_values, y_values, paras):
        """offset is the last in paras"""
        if not isinstance(x_values, np.ndarray):
            x_values = np.array(x_values)
        if not isinstance(y_values, np.ndarray):
            y_values = np.array(y_values)

        vert_factor = paras[0]
        x_shift = paras[1]
        y_shift = paras[2]
        waist_radius = paras[3]
        offset = paras[4]
        r_sq = (x_values - x_shift) ** 2 + (y_values - y_shift) ** 2
        z_values = vert_factor * np.exp(-2 * r_sq / waist_radius ** 2) + offset
        return z_values

    def guess(self, x_values, y_values, z_values):
        """for 'bumps' only     ******** ATTENTION WAS NEVER TESTED ***********
            offset is the last in paras
            z_values = vert_factor * np.exp(-2 *
                                        ((x_values - x_shift)**2 + (y_values - y_shift)**2) /
                                        waist_radius**2) + offset
            initial_parameters = [vert_factor, x_shift, y_shift, waist_radius, offset]
            """
        if not isinstance(x_values, np.ndarray):
            x_values = np.array(x_values)
        if not isinstance(y_values, np.ndarray):
            y_values = np.array(y_values)
        if not isinstance(z_values, np.ndarray):
            z_values = np.array(z_values)

        # suppose small noise -> don't smooth
        # set the easy-to-guess initial parameters
        offset = z_values.min()
        vert_factor = z_values.max() - offset
        (y_shift, x_shift) = np.unravel_index(z_values.argmax(), z_values.shape)

        # estimate 1/e2 waist radius: find the position(s) where 2 successive points are below the limit
        dec_lim = np.exp(-2)
        waist_idx = round(len(y_values) / 4)  # default value
        max_idx = y_values.argmax()
        diff_r = 0
        while ((max_idx + diff_r + 1 < len(y_values) - 2) and
               (((y_values[max_idx + diff_r] - offset) / vert_factor > dec_lim) or
                ((y_values[max_idx + diff_r + 1] - offset) / vert_factor > dec_lim))):
            diff_r += 1
        diff_g = 0
        while ((max_idx - diff_g - 1 > 0) and
               (((y_values[max_idx - diff_g] - offset) / vert_factor > dec_lim) or
                ((y_values[max_idx - diff_g - 1] - offset) / vert_factor > dec_lim))):
            diff_g += 1
        if (max_idx - diff_g - 1 > 0) and (max_idx + diff_r + 1 < len(y_values) - 2):
            waist_idx = round((diff_g + diff_r) / 2)
        else:
            if max_idx - diff_g - 1 > 0:
                waist_idx = diff_g
            if max_idx + diff_r + 1 < len(y_values) - 2:
                waist_idx = diff_r
        waist_radius = x_values[waist_idx] - x_values[0]

        initial_parameters = [vert_factor, x_shift, y_shift, waist_radius, offset]
        return initial_parameters


gauss2D = Gauss2D()


class Gauss2D_cst_offs(FitModel):
    """2D Gaussian with
    y_values = vert_factor *
      np.exp(-2 * ((x_values - x_shift) ** 2 + (y_values - y_shift) ** 2) / waist_radius ** 2 ) + offset"""

    def f(self, x_values, y_values, paras, offset=0):
        """offset is given separately (not in paras)"""
        if not isinstance(x_values, np.ndarray):
            x_values = np.array(x_values)
        if not isinstance(y_values, np.ndarray):
            y_values = np.array(y_values)

        vert_factor = paras[0]
        x_shift = paras[1]
        y_shift = paras[2]
        waist_radius = paras[3]
        r_sq = (x_values - x_shift) ** 2 + (y_values - y_shift) ** 2
        z_values = vert_factor * np.exp(-2 * r_sq / waist_radius ** 2) + offset
        return z_values

    def guess(self, x_values, y_values, z_values, offset=0):
        """for 'bumps' only
            offset is the last in paras
            z_values = vert_factor * np.exp(-2 *
                                        ((x_values - x_shift)**2 + (y_values - y_shift)**2) /
                                        waist_radius**2) + offset
            initial_parameters = [vert_factor, x_shift, y_shift, waist_radius, offset]
            """
        if not isinstance(x_values, np.ndarray):
            x_values = np.array(x_values)
        if not isinstance(y_values, np.ndarray):
            y_values = np.array(y_values)
        if not isinstance(z_values, np.ndarray):
            z_values = np.array(z_values)

        # suppose small noise -> don't smooth
        # set the easy-to-guess initial parameters
        vert_factor = z_values.max() - offset
        (y_shift, x_shift) = np.unravel_index(z_values.argmax(), z_values.shape)

        # estimate 1/e2 waist radius: find the position(s) where 2 successive points are below the limit
        dec_lim = np.exp(-2)
        waist_idx = round(len(y_values) / 4)  # default value
        max_idx = y_values.argmax()
        diff_r = 0
        while ((max_idx + diff_r + 1 < len(y_values) - 2) and
               (((y_values[max_idx + diff_r] - offset) / vert_factor > dec_lim) or
                ((y_values[max_idx + diff_r + 1] - offset) / vert_factor > dec_lim))):
            diff_r += 1
        diff_g = 0
        while ((max_idx - diff_g - 1 > 0) and
               (((y_values[max_idx - diff_g] - offset) / vert_factor > dec_lim) or
                ((y_values[max_idx - diff_g - 1] - offset) / vert_factor > dec_lim))):
            diff_g += 1
        if (max_idx - diff_g - 1 > 0) and (max_idx + diff_r + 1 < len(y_values) - 2):
            waist_idx = round((diff_g + diff_r) / 2)
        else:
            if max_idx - diff_g - 1 > 0:
                waist_idx = diff_g
            if max_idx + diff_r + 1 < len(y_values) - 2:
                waist_idx = diff_r
        waist_radius = x_values[waist_idx] - x_values[0]

        initial_parameters = [vert_factor, x_shift, y_shift, waist_radius]
        return initial_parameters


gauss2D_cst_offs = Gauss2D_cst_offs()


class GaussEll2D(FitModel):
    """Elliptic 2D Gaussian with long axis a rotated by theta (degrees)
    with respect to x-axis (positive theta goes up to negative y-values)
    paras = [vert_factor, cent_x, cent_y, waist_rad_a, waist_rad_b, theta, offset]
    idx           0          1      2          3            4         5       6 """

    def f(self, x_values, y_values, paras):
        """offset is the last in paras"""
        if not isinstance(x_values, np.ndarray):
            x_values = np.array(x_values)
        if not isinstance(y_values, np.ndarray):
            y_values = np.array(y_values)

        z_values = np.ones(x_values.shape) * np.nan

        vert_factor = paras[0]
        cent_x = paras[1]
        cent_y = paras[2]
        waist_rad_a = paras[3]
        waist_rad_b = paras[4]
        theta = paras[5]  # in degrees
        offset = paras[6]

        rot_matr = np.array([[np.cos(theta /180*np.pi), -np.sin(theta /180*np.pi)],
                             [np.sin(theta /180*np.pi), np.cos(theta /180*np.pi)]])

        for li in range(x_values.shape[0]):  # Treat data line by line
            # Represent the center (xc,yc) in the theta-rotated (a,b) coord system
            # cent_x, cent_y --> cent_a, cent_b
            cent_ab = rot_matr @ np.array([cent_x, cent_y])

            # Represent the positions of a line in the (a,b) coord system:
            li_posis_ab = rot_matr @ np.array([x_values[li], y_values[li]])
            # Calculate the values of a line in the (a,b) coord system using the simple formula
            z_values[li] = (vert_factor *
                            np.exp(-2 * (li_posis_ab[0] - cent_ab[0]) ** 2 / waist_rad_a ** 2) *
                            np.exp(-2 * (li_posis_ab[1] - cent_ab[1]) ** 2 / waist_rad_b ** 2)
                            + offset)
        return z_values

    def guess(self, x_values, y_values, z_values):
        """for 'bumps' only     ******** ATTENTION WAS NEVER TESTED ***********
            offset is the last in paras """
        if not isinstance(x_values, np.ndarray):
            x_values = np.array(x_values)
        if not isinstance(y_values, np.ndarray):
            y_values = np.array(y_values)
        if not isinstance(z_values, np.ndarray):
            z_values = np.array(z_values)

        # suppose small noise -> don't smooth
        # set the easy-to-guess initial parameters
        offset = z_values.min()
        vert_factor = z_values.max() - offset
        (y_shift, x_shift) = np.unravel_index(z_values.argmax(), z_values.shape)

        # estimate 1/e2 waist radius: find the position(s) where 2 successive points are below the limit
        dec_lim = np.exp(-2)
        waist_idx = round(len(y_values) / 4)  # default value
        max_idx = y_values.argmax()
        diff_r = 0
        while ((max_idx + diff_r + 1 < len(y_values) - 2) and
               (((y_values[max_idx + diff_r] - offset) / vert_factor > dec_lim) or
                ((y_values[max_idx + diff_r + 1] - offset) / vert_factor > dec_lim))):
            diff_r += 1
        diff_g = 0
        while ((max_idx - diff_g - 1 > 0) and
               (((y_values[max_idx - diff_g] - offset) / vert_factor > dec_lim) or
                ((y_values[max_idx - diff_g - 1] - offset) / vert_factor > dec_lim))):
            diff_g += 1
        if (max_idx - diff_g - 1 > 0) and (max_idx + diff_r + 1 < len(y_values) - 2):
            waist_idx = round((diff_g + diff_r) / 2)
        else:
            if max_idx - diff_g - 1 > 0:
                waist_idx = diff_g
            if max_idx + diff_r + 1 < len(y_values) - 2:
                waist_idx = diff_r
        waist_radius = x_values[waist_idx] - x_values[0]

        initial_parameters = [vert_factor, x_shift, y_shift, waist_radius, waist_radius, 2, offset]
        return initial_parameters


gaussEll2D = GaussEll2D()


class GaussEll2D_cst_offs(FitModel):
    """Elliptic 2D Gaussian with long axis a rotated by theta (degrees)
    with respect to x-axis (short axis b). Offset is given separately (not in paras)
    paras = [vert_factor, cent_x, cent_y, waist_rad_a, waist_rad_b, theta]
    idx           0          1      2          3            4         5  """

    def f(self, x_values, y_values, paras, offset=0):
        """offset is given separately (not in paras)"""
        all_paras = np.array(list(paras) + [offset])
        return gaussEll2D.f(x_values, y_values, all_paras)

    def guess(self, x_values, y_values, z_values, offset=0):
        """Attn never tested!!! For 'bumps' only. Offset is given separately (not in paras)"""
        return gaussEll2D.guess(x_values, y_values, z_values - offset)[:-1]


gaussEll2D_cst_offs = GaussEll2D_cst_offs()


class Exponential(FitModel):
    """single exponential increase or decrease.
    Recall that a * exp(b*(x-x0)) + c  =  a/exp(b*x0) * exp(b*x) + c
    So either a or x0 makes sense, not both together. Here we use:
    y_values = pre_factor * np.exp(exp_factor * x_values) + offset """

    def f(self, x_values, paras):
        if not isinstance(x_values, np.ndarray):
            x_values = np.array(x_values)
        pre_factor = paras[0]
        exp_factor = paras[1]
        offset = paras[2]
        y_values = pre_factor * np.exp(exp_factor * x_values) + offset
        return y_values

    def guess(self, x_values, y_values):
        """for increasing and decreasing exponentials
        offset is the last in paras
        y_values = pre_factor * np.exp(exp_factor * x_values) + offset
        initial_parameters = [pre_factor, exp_factor, offset]
        with exp_factor = +/- 1
        """
        if not isinstance(x_values, np.ndarray):
            x_values = np.array(x_values)
        if not isinstance(y_values, np.ndarray):
            y_values = np.array(y_values)

        # increase moving average box until min rel variation < rel_dev_lim
        # Stop smoothing if at any position (left, middle, right) the curve is 'horizontal' within rel_dev_lim
        rel_dev_lim = 0.01  # 1%
        box_pts_max = len(y_values) // 11  # keep at least 11 independent intervals
        if box_pts_max % 2 != 0:
            box_pts_max += 1  # make it even (and larger)
        box_pts = 1  # start with box of 3 points
        rel_d = self.rel_dev(y_values, box_pts)  # get minimum relative deviation of original data
        y_values_backup = y_values.copy()
        x_values_backup = x_values.copy()
        while (box_pts < box_pts_max) and (rel_d > rel_dev_lim):
            box_pts += 2  # stay with odd numbers
            x_values, y_values = self.moving_average(x_values_backup, y_values_backup, box_pts)
            rel_d = self.rel_dev(y_values, box_pts)

        # y_values = pre_factor * np.exp(exp_factor * x_values) + offset
        # set the easy to guess initial parameters
        offset = y_values.min()
        if y_values.argmax() < y_values.argmin():
            exp_factor = -1
        else:
            exp_factor = 1
        x1 = x_values[y_values.argmax()]
        pre_factor = np.exp(-exp_factor * x1) * (y_values.max() - offset)

        initial_parameters = [pre_factor, exp_factor, offset]
        return initial_parameters


exponential = Exponential()


class Logarithm(FitModel):
    """single exponential increase or decrease.
    Recall that a * log(b*(x-x0)) + c  =  a*log(x-x0) + c + a*log(b)
    So either b or c makes sense, not both together. Here we use:
    y_values = vert_factor * np.log(x_values - x_shift) + offset """

    def f(self, x_values, paras):
        """offset is the last in paras"""
        if not isinstance(x_values, np.ndarray):
            x_values = np.array(x_values)

        vert_factor = paras[0]
        x_shift = paras[1]
        offset = paras[2]
        y_values = vert_factor * np.log(x_values - x_shift) + offset
        return y_values

    def guess(self, x_values, y_values):  # TODO : Improve this
        """
        offset is the last in paras
        y_values = vert_factor * np.log(x_values - x_shift) + offset
        initial_parameters = [vert_factor, x_shift, offset]
        """
        if not isinstance(x_values, np.ndarray):
            x_values = np.array(x_values)
        if not isinstance(y_values, np.ndarray):
            y_values = np.array(y_values)

        # increase moving average box until min rel variation < rel_dev_lim
        # Stop smoothing if at any position (left, middle, right) the curve is 'horizontal' within rel_dev_lim
        rel_dev_lim = 0.01  # 1%
        box_pts_max = len(y_values) // 11  # keep at least 11 independent intervals
        if box_pts_max % 2 != 0:
            box_pts_max += 1  # make it even (and larger)
        box_pts = 1  # start with box of 3 points
        rel_d = self.rel_dev(y_values, box_pts)  # get minimum relative deviation of original data
        y_values_backup = y_values.copy()
        x_values_backup = x_values.copy()
        while (box_pts < box_pts_max) and (rel_d > rel_dev_lim):
            box_pts += 2  # stay with odd numbers
            x_values, y_values = self.moving_average(x_values_backup, y_values_backup, box_pts)
            rel_d = self.rel_dev(y_values, box_pts)

        # y_values = vert_factor * np.log(x_values - x_shift) + offset
        # set the easy to guess initial parameters
        offset = y_values.mean()
        vert_factor = 1
        x_shift = 1.2 * x_values.min()
        initial_parameters = [vert_factor, x_shift, offset]
        return initial_parameters


logarithm = Logarithm()


class Polynom(FitModel):
    """A polynomial of variable degree """
    polynom_degree = None

    def f(self, x_values, paras, degree=-10):

        """degree may be omitted.
        It then depends on len(paras)
        offset is the last in paras"""
        if not isinstance(x_values, np.ndarray):
            x_values = np.array(x_values)
        if not isinstance(paras, np.ndarray):
            paras = np.array(paras)

        if degree == -10:
            degree = len(paras) - 1  # a constant has degree zero
        if degree != len(paras) - 1:
            print("Polynom warning: Wrong number of parameters. Truncating or padding higher orders.")
            if degree > len(paras) - 1:
                paras = np.concatenate((np.zeros(degree - len(paras) + 1), paras))
            else:
                paras = paras[-(degree + 1):]
        # print("paras: ", paras)
        self.polynom_degree = len(paras) - 1

        y_values = np.zeros(x_values.shape)
        for exposant in range(len(paras)):
            y_values += paras[-1 - exposant] * x_values ** exposant
        return y_values

    def guess(self, x_values, y_values, degree=-10):
        """even higher order polynomials are initialized
        by a straight line: initial_parameters = [slope, offset]
        """
        if not isinstance(x_values, np.ndarray):
            x_values = np.array(x_values)
        if not isinstance(y_values, np.ndarray):
            y_values = np.array(y_values)

        # increase moving average box until min rel variation < rel_dev_lim
        # Stop smoothing if at any position (left, middle, right) the curve is 'horizontal' within rel_dev_lim
        rel_dev_lim = 0.02  # 2%
        box_pts_max = len(y_values) // 11  # keep at least 11 independent intervals
        if box_pts_max % 2 != 0:
            box_pts_max += 1  # make it even (and larger)
        box_pts = 1  # start with box of 3 points
        rel_d = self.rel_dev(y_values, box_pts)  # get minimum relative deviation of original data
        y_values_backup = y_values.copy()
        x_values_backup = x_values.copy()
        while (box_pts < box_pts_max) and (rel_d > rel_dev_lim):
            box_pts += 2  # stay with odd numbers
            x_values, y_values = self.moving_average(x_values_backup, y_values_backup, box_pts)
            rel_d = self.rel_dev(y_values, box_pts)

        # initialize to a straight line through first and last smoothed point
        offset = (x_values[-1] * y_values[0] - x_values[0] * y_values[-1]) / (x_values[-1] - x_values[0])
        slope = (y_values[-1] - y_values[0]) / (x_values[-1] - x_values[0])

        if degree == -10:
            degree = self.polynom_degree

        if degree == 1:
            initial_parameters = [slope, offset]
        elif degree == 0:
            initial_parameters = [offset]
        else:
            initial_parameters = np.concatenate((np.zeros(degree - 1), [slope, offset]))

        return initial_parameters


poly_var = Polynom()


class Poly00(Polynom):
    """A polynomial of degree 0 (a constant)"""

    def f(self, x_values, paras):
        return super().f(x_values, paras, degree=0)

    def guess(self, x_values, y_values):
        return super().guess(x_values, y_values, degree=0)


poly00 = Poly00()


class Poly01(Polynom):
    """A polynomial of degree 1 (a straight line)"""

    def f(self, x_values, paras):
        return super().f(x_values, paras, degree=1)

    def guess(self, x_values, y_values):
        return super().guess(x_values, y_values, degree=1)


poly01 = Poly01()


class Poly02(Polynom):
    """A polynomial of degree 2 (a parabola)"""

    def f(self, x_values, paras):
        return super().f(x_values, paras, degree=2)

    def guess(self, x_values, y_values):
        return super().guess(x_values, y_values, degree=2)


poly02 = Poly02()


class Poly03(Polynom):
    """A polynomial of degree 3"""

    def f(self, x_values, paras):
        return super().f(x_values, paras, degree=3)

    def guess(self, x_values, y_values):
        return super().guess(x_values, y_values, degree=3)


poly03 = Poly03()


class Poly04(Polynom):
    """A polynomial of degree 4"""

    def f(self, x_values, paras):
        return super().f(x_values, paras, degree=4)

    def guess(self, x_values, y_values):
        return super().guess(x_values, y_values, degree=4)


poly04 = Poly04()


class Poly05(Polynom):
    """A polynomial of degree 4"""

    def f(self, x_values, paras):
        return super().f(x_values, paras, degree=5)

    def guess(self, x_values, y_values):
        return super().guess(x_values, y_values, degree=5)


poly05 = Poly05()


class Poly06(Polynom):
    """A polynomial of degree 4"""

    def f(self, x_values, paras):
        return super().f(x_values, paras, degree=6)

    def guess(self, x_values, y_values):
        return super().guess(x_values, y_values, degree=6)


poly06 = Poly06()


class Poly07(Polynom):
    """A polynomial of degree 4"""

    def f(self, x_values, paras):
        return super().f(x_values, paras, degree=7)

    def guess(self, x_values, y_values):
        return super().guess(x_values, y_values, degree=7)


poly07 = Poly07()


class Poly08(Polynom):
    """A polynomial of degree 4"""

    def f(self, x_values, paras):
        return super().f(x_values, paras, degree=8)

    def guess(self, x_values, y_values):
        return super().guess(x_values, y_values, degree=8)


poly08 = Poly08()


class Poly09(Polynom):
    """A polynomial of degree 4"""

    def f(self, x_values, paras):
        return super().f(x_values, paras, degree=9)

    def guess(self, x_values, y_values):
        return super().guess(x_values, y_values, degree=9)


poly09 = Poly09()


class Poly10(Polynom):
    """A polynomial of degree 4"""

    def f(self, x_values, paras):
        return super().f(x_values, paras, degree=10)

    def guess(self, x_values, y_values):
        return super().guess(x_values, y_values, degree=10)


poly10 = Poly10()


class Poly11(Polynom):
    """A polynomial of degree 4"""

    def f(self, x_values, paras):
        return super().f(x_values, paras, degree=11)

    def guess(self, x_values, y_values):
        return super().guess(x_values, y_values, degree=11)


poly11 = Poly11()


class Poly12(Polynom):
    """A polynomial of degree 4"""

    def f(self, x_values, paras):
        return super().f(x_values, paras, degree=12)  # calls the f method of the parent class
        # return Polynom.f(self, x_values, paras, degree=12)  # Seems to be bad practice, but it works too

    def guess(self, x_values, y_values):
        return super().guess(x_values, y_values, degree=12)  # calls the guess method of the parent class
        # return Polynom.guess(self, x_values, y_values, degree=12)  # Seems to be bad practice, but it works too


poly12 = Poly12()

if __name__ == "__main__":
    # If the script part is in the __name__ == "__main__" block, the py file can be used
    # as a module without any modification.
    # So the script part should contain tests and applications of the functions
    # and classes defined before.

    # gauss1D
    simul_model = gauss1D
    print("\n--------------------------------------------------------")
    print("\n--------------------------------------------------------")
    print("Noisy", type(simul_model).__name__, "data - negligible uncertainty of each data point")
    # Generate noisy data
    # y_values = vert_factor * np.exp(-2 * ((x_values - x_shift) / waist_radius) ** 2) + offset
    x_data, y_data = simul_data(simul_model, [1.5, -0.5, 1.5, 3], 0.02, -2, 4)
    #                     simul_data(simul_model, paras1, noise, x_min, x_max)
    print("Real", type(simul_model).__name__, "parameters:", [1.5, -0.5, 1.5, 3])

    ti_leastsq = using_leastsq(x_data, y_data, [gauss1D, poly08])

    ti_curve_fit = using_curve_fit(x_data, y_data, [gauss1D, poly08])

    """
    ti_leastsq_boot = using_boot_leastsq(x_data, y_data, [gauss1D])

    ti_minimize = using_minimize(x_data, y_data, [gauss1D, poly08])

    print("\n--------------------------------------------------------")
    print("\nAverage fit-time summary: absolute values in ms")
    print("\t\t\tleastsq\t\tcurve_fit\tminimize")
    print("gauss1D:\t{:.3f}\t\t{:.3f}\t\t{:.3f}".format(
        ti_leastsq[0] * 1000, ti_curve_fit[0] * 1000, ti_minimize[0] * 1000))
    print("poly08:\t\t{:.3f}\t\t{:.3f}\t\t{:.3f}".format(
        ti_leastsq[1] * 1000, ti_curve_fit[1] * 1000, ti_minimize[1] * 1000))
    print("\n'gauss1D' has 4 parameters, 'poly08' has 9 parameters")

    print("\nAverage fit-time summary: relative values")
    print("\t\t\tleastsq\t\tcurve_fit\tminimize")
    fastest = min([ti_leastsq[0], ti_curve_fit[0], ti_minimize[0]])
    print("gauss1D:\t{:.3f}\t\t{:.3f}\t\t{:.3f}".format(
        ti_leastsq[0] / fastest, ti_curve_fit[0] / fastest, ti_minimize[0] / fastest))
    fastest = min([ti_leastsq[1], ti_curve_fit[1], ti_minimize[1]])
    print("poly08:\t\t{:.3f}\t\t{:.3f}\t\t{:.3f}".format(
        ti_leastsq[1] / fastest, ti_curve_fit[1] / fastest, ti_minimize[1] / fastest))

    print('\n\n------ fit the parameters 1by1 -----------------')
    pars_0 = np.array(gauss1D.guess(x_data, y_data))
    print("pars_0 = ")
    print(pars_0)
    pfit_1by1 = leastsq_1by1_fit(gauss1D.f, pars_0, x_data, y_data)
    print("pfit_1by1 = ")
    print(pfit_1by1)
    pfit_simult, success = opt.leastsq(gauss1D.residuals, pars_0,
                                       args=(x_data, y_data), full_output=False, epsfcn=0.0001)
    print("pfit_simult = ")
    print(pfit_simult)
    pfit_simult_after_1by1, success = opt.leastsq(gauss1D.residuals, pfit_1by1,
                                                  args=(x_data, y_data), full_output=False, epsfcn=0.0001)
    print("pfit_simult_after_1by1 = ")
    print(pfit_simult_after_1by1)
    """

    # Test the sot_r_gau fit model
    """
    peak_flu = paras[0]
    w = paras[1]
    y_values = np.zeros(x_values.shape)
    y_values[x_values < peak_flu] = np.pi * w**2 / 2 * np.log(peak_flu / x_values[x_values < peak_flu])
    """
    x_vals, y_vals = simul_data(sot_r_gau, [30, 30], rel_noise=0.05, x_mi=0.1, x_ma=23, num=250)
    #            init with guess: np.array([21, 5])
    ti_leastsq = using_leastsq(x_vals, y_vals, [sot_r_gau])

def the_end():
    pass


plt.show()

"""
I have defined a function to fit a sum of Gaussian and Lorentzian:

def mix(x,*p):
    ng = numg
    p1 = p[:3*ng]
    p2 = p[3*ng:]
    a = sumarray(gaussian(x,p1),lorentzian(x,p2))
    return a

leastsq,covar = opt.curve_fit(mix,energy,intensity,inputtot)

At the moment numg (the number of Gaussian shapes) is a global variable. Is there's any way that 
it can be incorporated into curve_fit as an extra argument instead, as can be done with leastsq
-----
The great thing about python is that you can define functions that return other functions, try currying:

def make_mix(numg): 
    def mix(x, *p): 
        ng = numg
        p1 = p[:3*ng]
        p2 = p[3*ng:]
        a = sumarray(gaussian(x,p1),lorentzian(x,p2))
        return a
    return mix

and then

leastsq, covar = opt.curve_fit(make_mix(numg),energy,intensity,inputtot)

"""
