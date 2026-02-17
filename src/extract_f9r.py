import tarfile
import lzma
from struct import unpack

import numpy as np
from pathlib import Path

known_unhandled={
    (0x02,0x13):"UBX-02-13 not listed in F9R docs",
(0x0a,0x36):"UBX-MON-COMMS, port information",
(0x02,0x15):"UBX-RXM-RAWX, raw observables",
(0x01,0x07):"UBX-NAV-PVT",
(0x01,0x13):"UBX-NAV-HPPOSECEF",
(0x01,0x01):"UBX-NAV-POSECEF",
(0x01,0x14):"UBX-NAV-HPPOSLLH",
(0x01,0x11):"UBX-NAV-VELECEF",
(0x01,0x35):"UBX-NAV-SAT",
(0x01,0x03):"UBX-NAV-STATUS",
(0x01,0x04):"UBX-NAV-DOP",
(0x01,0x20):"UBX-NAV-TIMEGPS",
    (0x01,0x21):"UBX-NAV-TIMEUTC",
    (0x01,0x36):"UBX-NAV-COV",
    (0x10,0x10):"UBX-ESF-STATUS",
    (0x10,0x15):"UBX-ESF-INS",
    (0x01,0x61):"UBX-NAV-EOE",
    (0x0a,0x38):"UBX-MON-RF",
    (0x0a,0x31): "UBX-MON-SPAN",
    (0x01, 0x34): "UBX-NAV-ORB",
    (0x01, 0x43): "UBX-NAV-SIG",
    (0x01, 0x22): "UBX-NAV-CLOCK",
    (0x01, 0x32): "UBX-NAV-SBAS",
    (0x10, 0x14): "UBX-ESF-ALG",
}

# Adjust these paths as needed
tar_path = Path('data/fluttershy_2026-02-06.tar')  # e.g., 'zed_f9r_data.tar'
# Assuming the decompressed streams are raw binary IMU samples.
# You will need to replace the parsing section below with the exact format of your files.
# Common possibilities for ZED-F9R raw logs:
#   - Fixed-size structs (e.g., uint64 timestamp + int32/int64 gyros/accels)
#   - UBX protocol messages (sync 0xb5 0x62, variable length)
# Provide details on the exact binary layout if this needs tuning.

# Containers to accumulate parsed data across all 144 files
# We'll collect as numpy arrays for efficient Allan variance later
accs = {}
t_accs=[]# seconds or ticks – convert to float seconds if needed
gyros={}
t_gyros = []  # seconds or ticks – convert to float seconds if needed
t_tps=[]
t_acc_last=None
i_acc_last=None
t_gyro_last=None
i_gyro_last=None
with tarfile.open(tar_path, 'r') as tar:
    # Sort members by name to preserve chronological order (common in segmented logs)
    members = sorted(tar.getmembers(), key=lambda m: m.name)

    for member in members:
        if member.isfile() and member.name.endswith('.xz'):
            print(f"Processing {member.name} ...")

            # Open the compressed member as a stream
            with tar.extractfile(member) as compressed_file:
                with lzma.open(compressed_file) as xz_file:
                    chunk = xz_file.read()  # slurp the whole file so we don't worry about chunk boundaries

                    i_chunk=0
                    while i_chunk<len(chunk):
                        if chunk[i_chunk]==0xb5: #ublox header
                            mu,b,pktcls,pktid,pktlen=unpack("<ccBBH",chunk[i_chunk:i_chunk+6])
                            i_chunk+=6
                            payload=chunk[i_chunk:i_chunk+pktlen]
                            i_chunk+=pktlen
                            cksum_a,cksum_b=chunk[i_chunk:i_chunk+2]
                            i_chunk+=2
                            if pktcls==0x10 and pktid==0x02:
                                x_gyro=None
                                y_gyro=None
                                z_gyro=None
                                x_acc=None
                                y_acc=None
                                z_acc=None
                                # Time tag definitely does roll over, just not in the context of the one day 2026-02-06
                                # that we are examining. Treat it as a unique key. Rollover is in
                                # 4Gi milliseconds=4Mi seconds, over 45 days between.
                                timeTag,flags,providerid=unpack("<IHH",payload[0:8])
                                timemark_sent=flags>>0 & 0b11
                                timemark_edge=flags>>2 & 0b1
                                n_meas=flags>>11 & 0b11111
                                words=unpack("<"+"I"*n_meas,payload[8:8+n_meas*4])
                                fields=[word >> 0 & 0xFFFFFF for word in words]
                                ids=[word>>24 & 0b111111 for word in words]
                                for dataid,field in zip(ids,fields):
                                    if dataid==10: #wheel tick
                                        pass
                                    elif dataid==14: #x_gyro
                                        if field>0x7F_FF_FF:
                                            field-=0x1_00_00_00
                                        x_gyro=field/2**12
                                    elif dataid==13: #z_gyro
                                        if field>0x7F_FF_FF:
                                            field-=0x1_00_00_00
                                        y_gyro=field/2**12
                                    elif dataid == 5:  # z_gyro
                                        if field > 0x7F_FF_FF:
                                            field -= 0x1_00_00_00
                                        z_gyro = field / 2 ** 12
                                    elif dataid == 12:  # T_gyro
                                        if field > 0x7F_FF_FF:
                                            field -= 0x1_00_00_00
                                        T_gyro = field / 1e2
                                    elif dataid == 16:  # x_acc
                                        if field > 0x7F_FF_FF:
                                            field -= 0x1_00_00_00
                                        x_acc = field / 2 ** 10
                                    elif dataid == 17:  # z_acc
                                        if field > 0x7F_FF_FF:
                                            field -= 0x1_00_00_00
                                        y_acc = field / 2 ** 10
                                    elif dataid == 18:  # z_acc
                                        if field > 0x7F_FF_FF:
                                            field -= 0x1_00_00_00
                                        z_acc = field / 2 ** 10
                                    else:
                                        print(f"Unrecognized dataid {dataid}")
                                if x_acc is not None:
                                    t_acc=timeTag
                                    t_accs.append(t_acc)
                                    accs[timeTag]=(x_acc,y_acc,z_acc)
                                if x_gyro is not None:
                                    t_gyro = timeTag
                                    t_gyros.append(t_gyro)
                                    gyros[timeTag]=(x_gyro,y_gyro,z_gyro,T_gyro)
                            elif pktcls == 0x0d and pktid == 0x01:
                                # UBX-TIM-TP
                                towMS,towSubMS,qErr,week,flags1,flags2=unpack("<IIiHBB",payload)
                                tow=towMS/1000+towSubMS/2**32
                                t_tps.append(tow)
                                if t_acc_last is not None:
                                    n_acc=len(t_accs)-i_acc_last
                                    t_acc_nextlast=t_acc_last
                                    dt_acc_last=t_accs[-1]-t_acc_nextlast
                                    if dt_acc_last<0:
                                        print(f"{t_accs[-1]=},{t_acc_nextlast=}")
                                    dt_tp=t_tps[-1]-t_tps[-2]
                                    day=tow//(3600*24)
                                    tow_r=tow%(3600*24)
                                    hour=tow_r//3600
                                    tow_r=tow_r%3600
                                    min=tow_r//60
                                    sec=tow_r%60
                                    try:
                                        print(f"{day:1.0f}-{hour:02.0f}:{min:02.0f}:{sec:06.3f},{n_acc=:4d},{dt_acc_last=:4d},ticksize={float(dt_tp)/float(dt_acc_last)}")
                                    except:
                                        print(f"{day:1.0f}-{hour:02.0f}:{min:02.0f}:{sec:06.3f},{n_acc=:4d},{dt_acc_last=:4d},ticksize=Inf")
                                t_acc_last=t_accs[-1]
                                i_acc_last=len(t_accs)
                                dt_acc_last=t_acc_last
                                if t_gyro_last is not None:
                                    n_gyro=len(t_gyros)-i_gyro_last
                                    t_gyro_nextlast=t_gyro_last
                                    dt_gyro_last=t_gyros[-1]-t_gyro_nextlast
                                    if dt_gyro_last<0:
                                        print(f"{t_gyros[-1]=},{t_gyro_nextlast=}")
                                    dt_tp=t_tps[-1]-t_tps[-2]
                                    day=tow//(3600*24)
                                    tow_r=tow%(3600*24)
                                    hour=tow_r//3600
                                    tow_r=tow_r%3600
                                    min=tow_r//60
                                    sec=tow_r%60
                                    try:
                                        print(f"{day:1.0f}-{hour:02.0f}:{min:02.0f}:{sec:06.3f},{n_gyro=:4d},{dt_gyro_last=:4d},ticksize={float(dt_tp)/float(dt_gyro_last)}")
                                    except:
                                        print(f"{day:1.0f}-{hour:02.0f}:{min:02.0f}:{sec:06.3f},{n_gyro=:4d},{dt_gyro_last=:4d},ticksize=Inf")
                                t_gyro_last=t_gyros[-1]
                                i_gyro_last=len(t_gyros)
                                dt_gyro_last=t_gyro_last
                            elif (pktcls, pktid) in known_unhandled:
                                pass
                            else:
                                print(f"Unhandled packet 0x{pktcls:02x}-0x{pktid:02x}, len {pktlen}")
                        else:
                            i_chunk+=1

                    print(f"  Read {len(chunk)} bytes from this chunk")

# Convert to numpy arrays (float64 for Allan tools)
t_accs,x_accs,y_accs,z_accs=[],[],[],[]
for t_acc,(x_acc,y_acc,z_acc) in accs.items():
    t_accs.append(t_acc/1000)
    x_accs.append(x_acc)
    y_accs.append(y_acc)
    z_accs.append(z_acc)
t_accs = np.array(t_accs, dtype=np.float64)
x_accs = np.array(x_accs, dtype=np.float64)
y_accs = np.array(y_accs, dtype=np.float64)
z_accs = np.array(z_accs, dtype=np.float64)

t_gyros,x_gyros,y_gyros,z_gyros,T_gyros=[],[],[],[],[]
for t_gyro,(x_gyro,y_gyro,z_gyro,T_gyro) in gyros.items():
    t_gyros.append(t_gyro/1000)
    x_gyros.append(x_gyro)
    y_gyros.append(y_gyro)
    z_gyros.append(z_gyro)
    T_gyros.append(T_gyro)
t_gyros = np.array(t_gyros, dtype=np.float64)
x_gyros = np.array(x_gyros, dtype=np.float64)
y_gyros = np.array(y_gyros, dtype=np.float64)
z_gyros = np.array(z_gyros, dtype=np.float64)
T_gyros = np.array(T_gyros, dtype=np.float64)

save_path = 'data/zed_f9r_processed.npz'  # Choose your filename/path
np.savez_compressed(
    save_path,
    t_accs=t_accs,
    x_accs=x_accs,
    y_accs=y_accs,
    z_accs=z_accs,
    t_gyros=t_gyros,
    x_gyros=x_gyros,
    y_gyros=y_gyros,
    z_gyros = z_gyros,
    T_gyros = T_gyros
)
