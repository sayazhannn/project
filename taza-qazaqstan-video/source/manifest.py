import glob, hashlib, os
UP="/root/.claude/uploads/6f3f2afd-bfea-59e0-987f-4889abb6a1cb/"
def P(ids): return [UP+i+"-image.jpg" for i in ids.split()]
FR={
2:"277ad7f4 537a3aa9 127e8c72 a1c15e87 724ffb19 c31b1130 da894e43 051edbfa 03f647aa f8e5b796 91a369d3 e3c372c8 f19634f8",
3:"db7e23df 1d02892e 6634a437 5a7dde16 0119d0f7 35f386a8 9c9a47fd 9452b35a 4552b5ec 38d99725 b3951894 12bb8623",
4:"b6094952 17662e9b 24017c59 6841be71 888f229b 6781e6d0 ccf4b3f5 f12b7022 75782d04 e2024f3f 086fe467 5981d210 d93c299e d811100a c0503e86 69499990 73bddd67 3b53ab42 5fcc3b9c",
5:"a26138a7 29272522 62e6e898 2cbe70c1 615dc10c a7b44d49 d4ea1857",
6:"e4e95e4b ac69bf52 cfae3d64 6dae7601 2ce6ffa8 00c51312 33d55e9c fc96174d 74c17555",
7:"f434f1ba 8164b1b7 e3b7b4dc f26a080f 13811c6f 3c22b275 4ec3cb2e a06c26d0",
8:"1294f9a7 f9f431a6 85335eb3 08d21caa",
9:"c7e64e5b ce4cb3a5",
10:"869db1f2 da5948e0 fca1154f 9a17182a cd3b7a6f d67bdba9 d2a9504d c806fd2b 244ba4cd 86561cbe 108d2558",
11:"6bc54ae2 fadfaf49",
12:"3ff71be8 cf600eb5 bc52e53a 5b59cbff f7097d50 77b54c73 291bd318 797d7eb7",
13:"d69219ee 3bcbe8b3 70a25639",
14:"8c2f8274",
15:"32f3204c",
16:"49f0ae8f c6249b9c dc39239b c562754e 4df0241f 1622bc58 ddaf3800 aa602ab6 bc9bb6e4 2e91a485 ef0008f5 70386fa9",
17:"6c6fd858 a0b0be60 c84d17ff 623781a8 ad651e34 7d717343 296ceb3f 6cf06b99 cfa1e030 dc96c292 5d001ae2 77151e04 23509004 6d60f532 ac408a9c 8282d7d9 0624a755 30caf619 5e33cbea 653ebe7c cfbee985 00cbf0cc f1f94d90 9fa71beb 69f2d2d8 e1b5c9ed",
18:"05e11933 8e150360 7b500a55 14a072b4 61d1f7d3 badfcc4e",
19:"9b01555e 2cf36ce9 200324b8 d2aa1246 3a4cd2bb c7aef9cf 7f29085a 27c701b4 1ae05d9e b5ec48a2 80da4557 76f60926 79db828d 60763d54 04f7ef83 af622d4a",
20:"084bb455 df473aa5",
}
LOGO=UP+"c5c55249-image.jpg"
def md5(p): return hashlib.md5(open(p,'rb').read()).hexdigest()
def thumb(p):
    from PIL import Image
    import numpy as np
    return np.asarray(Image.open(p).convert("RGB").resize((48,48)),float)
def frames():
    out={}
    for k,v in FR.items():
        seen=[]; L=[]
        for p in P(v):
            assert os.path.exists(p),p
            t=thumb(p)
            if any(abs(t-s).mean()<1.0 for s in seen): print("dup within frame",k,os.path.basename(p)); continue
            seen.append(t); L.append(p)
        out[k]=L
    return out
if __name__=="__main__":
    from PIL import Image
    F=frames(); tot=0
    for k in sorted(F):
        print(k,len(F[k])); tot+=len(F[k])
    print("total",tot)
    # cross-frame duplicates
    allh={}
    for k in sorted(F):
        for p in F[k]: allh.setdefault(md5(p),[]).append(k)
    print({h[:6]:v for h,v in allh.items() if len(v)>1})
    print(Image.open(LOGO).size, Image.open(UP+"32f3204c-image.jpg").size)
