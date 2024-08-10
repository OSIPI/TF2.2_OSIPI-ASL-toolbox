function y=W_FindScan(filepath,str)
% This script is for finding the scan containg keyword "str"
% processing, Dec. 14th, 2017
expno=W_Expno(filepath);
rec=[];
for ni=1:length(expno)
    tempno=expno(ni);
    filename=[filepath filesep num2str(tempno)];
    Para=W_ImgParaAbs(filename);
    if W_SubStr(str,Para.Protocol)
        rec=[rec tempno];
    end
end
y=rec;
end
        