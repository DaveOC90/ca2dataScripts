import os, sys, shutil
import time
import subprocess as subp
import glob
import pdb
import argparse 


def smrMatConv(ippath,oppath):

    process = subp.Popen(["matlab","-nosplash","-nodesktop","-r","[x]=convertSMRtoMAT('"+ippath+"','"+oppath+"');display(x);exit"], stdout=subp.PIPE, stderr=subp.PIPE)


    for line in iter(process.stdout.readline,b''):
        print('{}'.format(line.rstrip()))

    process.kill()





if __name__ == '__main__':


    parser=argparse.ArgumentParser(description='Run script to convert smr files to mat files')
    parser.add_argument('orgDir',type = str, help="Path to organized data directory")


    orgdir = parser.orgDir


    for root, dirs, fs in os.walk(orgdir):
        for f in fs:
            if f.endswith('.smr'):
                fpath = os.path.join(root,f)
                matpath = fpath.replace('.smr','.mat')
                print('Converting: ', fpath)
                smrMatConv(fpath,matpath)
                print('File written to:', matpath)
                
