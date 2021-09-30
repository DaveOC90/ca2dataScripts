function [x] = convertSMRtoMAT(ippath,oppath)

addpath son/;
fid=fopen(ippath,'rb+');
x=SONImportEdit(fid,oppath);

end
