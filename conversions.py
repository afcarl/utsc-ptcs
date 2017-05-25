
## Conversion functions
def dec_str2raw(s):
    f = [float(i) for i in s.split(":")]
    if f[0]<0.:
        dec = f[0]-f[1]/60.-f[2]/60./60. 
    else:
        dec = f[0]+f[1]/60.+f[2]/60./60. 
    return int(dec*1073741824.0/90.0)

def ra_str2raw(s):
    f = [float(i) for i in s.split(":")]
    ra = f[0]+f[1]/60.+f[2]/60./60.
    return int(ra*2147483648.0/12.0)

def dec_raw2str(raw):
    dec = float(raw)/1073741824.0*90.0
    return "%+02d:%02d:%02d" % (int(dec), int(abs(dec)%1*60), round(abs(dec)%1*60%1*60, 1))

def ra_raw2str(raw):
    ra = float(raw)/2147483648.0 *12.0
    return  "%02d:%02d:%02d" % (int(ra),  int(ra%1*60),  round(ra%1*60%1*60, 1)) 

__all__ = ["dec_str2raw","ra_str2raw","dec_raw2str","ra_raw2str"]
