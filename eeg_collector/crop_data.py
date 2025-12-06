import mne

file = "data/KONRAD-4_ruszanie_run1_20251202_205706_raw.fif"

raw = mne.io.read_raw_fif(file, preload=True)
print(raw.info)
raw.crop(tmin=520)
raw.plot()
raw.save(fname="data/KONRAD-4_ruszanie_run1_20251202_205706_raw_cropped.fif")
        
