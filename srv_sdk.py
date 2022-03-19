# < imports >--------------------------------------------------------------------------------------

import socket
import select
import sys
import time

# -------------------------------------------------------------------------------------------------
def start(ft_datachannel, ft_target):
    """
    reconnect if we go too long with out a ping, the keepalive was a little too platform
    specific so it was easier just to add support right into the protocol instead
    """
    # connected flag
    lv_ds_connected = False

    # target socket
    tsock = None

    # last activity
    lastping = time.time() 

    # init buffer
    ls_buf = b""

    # keep running...
    while True:
        # datachannel is not connected ?  
        if not lv_ds_connected:
            # connect to datachannel
            try:
                # create datachannel socket
                dcs = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                # setup datachannel socket
                dcs.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                # connect to datachannel
                dcs.connect(ft_datachannel)
                # set the socket into blocking mode
                dcs.settimeout(None)
                # last activity
                lastping = time.time()

            # em caso de erro,...
            except Exception as e:
                # wait 5s
                time.sleep(5)
                # next try
                continue
                
            # datachannel is connected 
            lv_ds_connected = True

        # handlers to read
        lrd = [dcs]
        # handlers to write
        lwr = []
        # handlers with error
        ler = [dcs]

        # is target connected ?  
        if tsock is not None:
            # enable to read
            lrd.append(tsock)
            # enable to error
            ler.append(tsock)

        # monitors handlers until they become readable or writable, or a communication error occurs
        lrd, lwr, ler = select.select(lrd, lwr, ler, 1)

        # too long (20s) without a ping ?
        if time.time() - lastping > 20:
            # force reconnect
            lv_ds_connected = False
            # close datachannel socket
            dcs.close()
            # try again
            continue

        # data from target ?
        if tsock in lrd:
            # receive data from target
            data = tsock.recv(4096)
            # send all data via datachannel
            sendall(dcs, data)

        # data from datachannel ?
        if dcs in lrd:
            # receive data from datachannel 
            data = dcs.recv(4096)

            # no data ?
            if not data:
                # try to get connected again
                lv_ds_connected = False

                # is target connected  
                if tsock is not None:
                    # close target socket
                    tsock.close()
                    tsock = None

                # try again
                continue

            # append data in buffer
            ls_buf = ls_buf + data

            # process buffer
            while len(ls_buf) > 0:
                # get command
                li_cmd = ls_buf[0]

                # disconnect command ?
                if 0 == li_cmd:
                    # last activity
                    lastping = time.time()
                    # is target connected  
                    if tsock is not None:
                        # close target socket
                        tsock.close()
                        tsock = None

                    # adjust buffer (skip command byte)
                    ls_buf = ls_buf[1:]
                    # go next
                    continue

                # client connected command ?
                elif 1 == li_cmd:
                    # last activity
                    lastping = time.time()
                    # is target connected ?
                    if tsock is not None:
                        # close target socket
                        tsock.close()
                        tsock = None

                    # create target socket    
                    tsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    # connect to target
                    tsock.connect(ft_target)
                    # set the socket into blocking mode
                    tsock.settimeout(None)

                    # adjust buffer (skip command byte)
                    ls_buf = ls_buf[1:]

                # send data to target command ?
                elif 2 == li_cmd:
                    # last activity
                    lastping = time.time()

                    # data length (int 4 bytes)
                    li_sz = ls_buf[1] << 24 | ls_buf[2] << 16 | ls_buf[3] << 8 | ls_buf[4]

                    # valid buffer size ?
                    if len(ls_buf) >= (1 + 4 + li_sz):
                        # data
                        data = ls_buf[1 + 4:1 + 4 + li_sz]
                        # adjust buffer
                        ls_buf = ls_buf[1 + 4 + li_sz:]

                        # is target connected  
                        if tsock is not None:
                            # set socket into unblocking mode
                            tsock.settimeout(0)
                            # send all data
                            sendall(tsock, data)
                            # set socket into blocking mode
                            tsock.settimeout(None)

                    # senão,...
                    else:
                        # abort
                        break

                # keep alive cmd ?
                elif 3 == li_cmd:
                    # last activity
                    lastping = time.time()

                    # adjust buffer (skip command byte)
                    ls_buf = ls_buf[1:]

                # senão,...
                else:
                    # unknown command
                    raise Exception("unknown command")

# -------------------------------------------------------------------------------------------------
def sendall(f_sock, f_data):

    # for all data bytes...
    while len(f_data) > 0:
        try:
            # send data
            li_sent = f_sock.send(f_data)
            # adjust data buffer 
            f_data = f_data[li_sent:]

        # em caso de erro,...    
        except BlockingIOError:
            # log
            print("blocking io error")

# -------------------------------------------------------------------------------------------------
def main():
    """
    drive app
    """
    # the first argument is the datachannel address, and the second argument is the target address.
    llst_args = sys.argv

    # error in args ?
    if len(llst_args) < 3:
        # log
        print("<datachannel-ip>:<datachannel-port> <target-ip>:<target-port>")
        # quit
        exit()

    # datachannel endpoint
    llst_datachannel = llst_args[1].split(':')
    # datachannel port
    llst_datachannel[1] = int(llst_datachannel[1])
    # datachannel addr
    lt_datachannel = tuple(llst_datachannel)

    # target endpoint
    llst_target = llst_args[2].split(':')
    # target port
    llst_target[1] = int(llst_target[1])
    # target addr
    lt_target = tuple(llst_target)

    # the address and port pairs are for a TCP/IP connection.
    # ("192.168.15.101", 61001), ("rpi-cam", 5900)
    start(lt_datachannel, lt_target)

# -------------------------------------------------------------------------------------------------

main()

# < the end >--------------------------------------------------------------------------------------
