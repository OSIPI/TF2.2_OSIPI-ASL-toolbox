function[CBF]=Tested_CBF_calculation_single_voxel_mouse(X)
% Script made by Valerio Zerbi, 2015
% First, you must load the file
% X = double(squeeze(analyze75read('image_FAIR_EPI.hdr')));

CBF = zeros(96,128);

%optionally, output the T1_selective and T1_global
%T1_sel2 = zeros(96,128);
%T1_glo2 = zeros(96,128);

%Note: the TI data are coupled with the modified FAIR-EPI MR sequence by Valerio Zerbi and Giovanna Ielacqua.
xdata = [0.026816965935356 0.086816965935356 0.186816965935356 0.286816965935356 0.386816965935356 0.486816965935356 0.586816965935356 0.786816965935356 0.986816965935356 1.18681696593536 1.48681696593536 1.78681696593536 2.08681696593536 2.38681696593536 2.68681696593536 2.98681696593536];


sel = X(:,:,[1:16]);
sel = squeeze(double(sel));

glo = X(:,:,[17:32]);
glo = squeeze(double(glo));


%Select the ROI
close all
imshow(X(:,:,1),[],'Border','tight'),title('Select ROI')
screen_size = get(0, 'ScreenSize');
f1 = figure(1);
set(f1, 'Position', [0 0 screen_size(3) screen_size(4) ] );
[x, y, Ir, xi, yi] = roipoly;
In = double(Ir);

for z=1:16
    A(:,:,z)=In.*glo(:,:,z);
    B(:,:,z)=In.*sel(:,:,z);
end

s = size(A);

for x=1:s(1)
    for y=1:s(2)
        
        if A(x,y,1) ~= 0
            [T1_glo,T1_glo_TT]=T1fit(xdata,reshape(A(x,y,:),1,16));
            [T1_sel,T1_sel_TT]=T1fit(xdata,reshape(B(x,y,:),1,16));
            CBF(x,y) = 4980*T1_glo/2250*(1000/T1_sel-1000/T1_glo);
        end
    end
end
        
        
%optionally, output the T1_selective and T1_global
%T1_glo2 = T1_glo;
%T1_sel2 = T1_sel;
%Results = [CBF; T1_glo2; T1_sel2]';
