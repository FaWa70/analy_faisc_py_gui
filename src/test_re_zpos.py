import re

def extract_z_from_filename(fi):
    z = -20e20
    # extract the position floating point number from the string fi
    rr = re.findall(r"[-+]?[.]?[\d]+(?:,\d\d\d)*[\.|\,|p]?\d*(?:[eE][-+]?\d+)?", fi)
    zz = rr[0]
    zz = zz.replace(",", ".")
    zz = zz.replace("p", ".")
    z = float(zz)
    return z

name = "pos5.1248 f541mm"
print("\n", name)
print(extract_z_from_filename(name))

name = "pos-4p55478mm"
print("\n", name)
print(extract_z_from_filename(name))

name = "pos+004574,4mm"
print("\n", name)
print(extract_z_from_filename(name))