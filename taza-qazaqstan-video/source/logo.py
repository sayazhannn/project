import numpy as np
from PIL import Image
from manifest import LOGO
def cut_logo(out="logo.png"):
    im=np.asarray(Image.open(LOGO).convert("RGB"),np.float32)
    mn=im.min(axis=2)
    a=np.clip((255-mn-10)/(255-mn.min()-10+1e-6)*1.0,0,1)  # distance from white
    a=np.clip((255-mn-8)/150.0,0,1)
    a=np.where(a<0.04,0,a)
    af=np.maximum(a,1e-3)[...,None]
    rgb=np.clip((im-255*(1-af))/af,0,255)
    rgba=np.dstack([rgb,a*255]).astype(np.uint8)
    ys,xs=np.where(a>0.15)
    y0,y1,x0,x1=ys.min(),ys.max(),xs.min(),xs.max()
    pad=6
    rgba=rgba[max(0,y0-pad):y1+pad,max(0,x0-pad):x1+pad]
    Image.fromarray(rgba,"RGBA").save(out)
    print(rgba.shape)
if __name__=="__main__": cut_logo()
