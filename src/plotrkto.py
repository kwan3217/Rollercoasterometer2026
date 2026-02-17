import matplotlib.pyplot as plt
import numpy as np

with open("RKTO0620_fast.csv","rt") as inf:
    for line in inf:
        print(line)
        header=line.strip().split(",")
        for i in range(len(header)):
            header[i]=header[i].strip()
        break
    cols={}
    for col in header:
        cols[col]=[]
    for i_line,line in enumerate(inf):
        line=line.strip()
        parts=line.split(",")
        for i_part,(part,col) in enumerate(zip(parts,cols.values())):
            if i_part==1:
                col.append(float(part))
            else:
                col.append(int(part))
        if i_line%100==0:
            print(".",end="")
            if i_line%10000==0:
                print(i_line)
    tc=np.array(cols["tc"])
    max=np.array(cols["max"])/(32768.0/16.0)
    may=np.array(cols["may"])/(32768.0/16.0)
    maz=-np.array(cols["maz"])/(32768.0/16.0)
    mgx=np.array(cols["mgx"])/(32768.0/2000.0)
    mgy=np.array(cols["mgy"])/(32768.0/2000.0)
    mgz=np.array(cols["mgz"])/(32768.0/2000.0)
    plt.figure("Launch")
    plt.subplot(2,1,1)
    plt.title("Launch")
    w=np.logical_and(tc>-10,tc<100)
    plt.plot(tc[w],max[w],'r',label="X")
    plt.plot(tc[w],may[w],'g',label="Y")
    plt.plot(tc[w],maz[w],'b',label="Z (thrust)")
    plt.legend()
    plt.ylabel("Acceleration/g")
    plt.subplot(2,1,2)
    plt.plot(tc[w],mgx[w],'r',label="X")
    plt.plot(tc[w],mgy[w],'g',label="Y")
    plt.plot(tc[w],mgz[w],'b',label="Z (thrust)")
    plt.ylabel("Rotation/(deg/s)")
    plt.xlabel("Time from launch/s")
    plt.legend()

    plt.figure("Entry")
    plt.subplot(2, 1, 1)
    plt.title("Entry")
    w = np.logical_and(tc > 450, tc < 950)
    plt.plot(tc[w], max[w], 'r', label="X")
    plt.plot(tc[w], may[w], 'g', label="Y")
    plt.plot(tc[w], maz[w], 'b', label="Z (thrust)")
    plt.legend()
    plt.ylabel("Acceleration/g")
    plt.subplot(2, 1, 2)
    plt.plot(tc[w], mgx[w], 'r', label="X")
    plt.plot(tc[w], mgy[w], 'g', label="Y")
    plt.plot(tc[w], mgz[w], 'b', label="Z (thrust)")
    plt.ylabel("Rotation/(deg/s)")
    plt.xlabel("Time from launch/s")
    plt.legend()
    plt.show()
