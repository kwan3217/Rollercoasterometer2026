import struct
import matplotlib.pyplot as plt

with open("RKTO0500.SDS","rb") as inf,open("RKTO0500.SDS.tar.zpaq","wb") as zpaq:
    KwanSync=inf.read(8)
    done=False
    i_packet=0
    apid_stats={}
    tcs=[[],[],[],[],[],[],[],[],[],[],[],[],]
    axs=[]
    ays=[]
    azs=[]
    gxs=[]
    gys=[]
    gzs=[]
    bxs=[]
    bys=[]
    bzs=[]
    hxs=[]
    hys=[]
    hzs=[]
    mins=[0]*16
    last_tc=[0]*16
    while not done:
        header=inf.read(6)
        if len(header)!=6:
            done=True
            continue
        apid,seq,pktlen=struct.unpack(">HHH",header)
        has_sec_hdr=(apid & 0x800)>0
        apid=apid & 0x7FF
        pktlen+=1
        body=inf.read(pktlen)
        if len(body)!=pktlen:
            done=True
            continue
        if apid not in apid_stats:
            apid_stats[apid]=0
        apid_stats[apid]+=1
        if apid==0x003:
            zpaq.write(body)
        elif apid==0x006:
            tc,ax,ay,az,gx,gy,gz,mt=struct.unpack(">Ihhhhhhh",body)
            if tc<last_tc[apid]:
                mins[apid]+=1
            last_tc[apid]=tc
            tc=tc/60_000_000+mins[apid]*60.0
            for var,lst in zip((tc,ax,ay,az,gx,gy,gz),(tcs[apid],axs,ays,azs,gxs,gys,gzs)):
                lst.append(var)
        elif apid==0x004:
            tc,bx,by,bz=struct.unpack(">Ihhh",body)
            if tc<last_tc[apid]:
                mins[apid]+=1
            last_tc[apid]=tc
            tc=tc/60_000_000+mins[apid]*60.0
            for var,lst in zip((tc,bx,by,bz),(tcs[apid],bxs,bys,bzs)):
                lst.append(var)
        elif apid==0x00b:
            tc,hx,hy,hz,zero=struct.unpack(">Ihhhh",body)
            if tc<last_tc[apid]:
                mins[apid]+=1
            last_tc[apid]=tc
            tc=tc/60_000_000+mins[apid]*60.0
            for var,lst in zip((tc,hx,hy,hz),(tcs[apid],hxs,hys,hzs)):
                lst.append(var)
        i_packet+=1
        if i_packet%100==0:
            print(".",end="")
            if i_packet%10000==0:
                print(i_packet)
    print(i_packet)
    for k,v in apid_stats.items():
        print(f"{k:03x}: {v}")
    plt.plot(tcs[0x006],axs,label="max")
    plt.xlabel("T/s")
    plt.ylabel("Raw X (thrust) acceleration, DN")
    plt.show()