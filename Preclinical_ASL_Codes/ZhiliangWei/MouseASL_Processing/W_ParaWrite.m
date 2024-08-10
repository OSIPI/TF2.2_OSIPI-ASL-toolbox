function y=W_ParaWrite(dir,Para,choice)
% Write struct parameters into a .txt file
% dir: filepath directory
% Para: parameters to be stored, consistent with WeiF_ImgParaAbs function
if choice==0
    fp=fopen([dir filesep 'Parameters.txt'],'w');
else
    fp=fopen([dir filesep 'Parameters.txt'],'a');
end
fprintf(fp,'%s\r\n',[Para.path]);
fprintf(fp,'%s\r\n',[Para.Protocol]);
fprintf(fp,'%s\r\n',['ROI: ' num2str(fix(10*Para.ROI)/10)]);
fprintf(fp,'%s\r\n',['Thickness: ' num2str(Para.thickness)]);
fprintf(fp,'%s\r\n',['Size: ' num2str(Para.size)]);
fprintf(fp,'%s\r\n',['SliceNum: ' num2str(Para.slicenum)]);
fprintf(fp,'%s\r\n',['Unit: ' Para.Unit{1} Para.Unit{2}]);
fprintf(fp,'%s\r\n',['TR: ' num2str(Para.tr)]);
fprintf(fp,'%s\r\n',['TE: ' num2str(Para.te)]);
fprintf(fp,'%s\r\n',['eTE: ' num2str(Para.eTE)]);
fprintf(fp,'%s\r\n',['CPMG Num: ' num2str(Para.EchoNum)]);
fprintf(fp,'%s\r\n',['Post Label Time: ' num2str(Para.PostLabelTime)]);
fprintf(fp,'%s\r\n',['Slab: ' num2str(Para.SlabMargin) ' mm']);
fprintf(fp,'%s\r\n',['Segment: ' num2str(Para.Segment)]);
fprintf(fp,'%s\r\n',['Time: ' Para.ScanTime]);
fclose(fp);
end