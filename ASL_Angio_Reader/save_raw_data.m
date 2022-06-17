clear all;
[FileName,PathName] = uigetfile('*.*','Image file (*.REC)');
if isequal(FileName,0)|isequal(PathName,0)
    error('File not found');
end;
ss=1.00268e-003;
rs=6.60195 ;
ri=0.0;
xdim=96;
ydim=96;
TIdim=1;
slices=15;
dyn=20;


inputfile=fullfile(PathName,FileName);
[pathstr,name,ext,versn] = fileparts(inputfile);
outputfilebase=fullfile(pathstr,name);

fileid = fopen (inputfile, 'r');
data2 = (reshape(fread( fileid,xdim*ydim*slices*dyn, 'int16'),xdim,ydim,dyn,slices));
fclose(fileid);

single_slice_lab_ctrl=zeros(xdim,ydim,dyn);
for x=1:xdim
    for y=1:ydim
        for d=1:dyn
            single_slice_lab_ctrl(x,y,d)=data2(x,y,d,9);
        end
    end
end

single_slice_lab_ctrl=flipdim(single_slice_lab_ctrl,2);
size(single_slice_lab_ctrl)
perf2=make_nii(single_slice_lab_ctrl, [2.29 2.29 6.0])
save_nii(perf2, 'Q:\HELLE\ASL_Data\ASL Motion TEst 07.07.11\kiel_single_slice_lab_ctrl');