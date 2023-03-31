import numpy as np
import matplotlib.pyplot as plt

all_dat = np.array(list(range(10)) + [2, 2, 4, 5, 6, 6, 6]) * (-2)
good_idx = list(np.arange(10, step=2))
all_good_dat = all_dat[good_idx]

# Now use remove additionally positions 4 and 8
rem_this = [4, 8]
restr_good_idx1 = list(set(good_idx) - set(rem_this))
rest_good_dat1 = all_dat[restr_good_idx1]

# now make the same using all_good_dat as origin
restr_good_idx2 = [x for x in range(len(good_idx)) if (good_idx[x] not in rem_this)]
# ok this works, but I did not succeed with numpy array manipulation
rest_good_dat2 = all_good_dat[restr_good_idx2]

# TODO keep same bins
fig, axes = plt.subplots()
this_col = 'blue'
_, bins, _ = axes.hist(all_dat,
                       bins="auto",
                       fill=True,
                       linewidth=3,
                       edgecolor=this_col,
                       facecolor='none',
                       label="labeltext")
axes.hist(all_good_dat,
          bins=bins,
          color=this_col,
          label="labeltext2")
axes.hist(all_dat,
          bins=bins,
          fill=True,
          linewidth=3,
          edgecolor='red',
          facecolor='none',
          label="labeltext")
axes.legend()
axes.set_aspect("auto")