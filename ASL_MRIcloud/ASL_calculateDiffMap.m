function ASL_calculateDiffMap(path_temp,asl_paras)
% Calculate difference map and write out the .img/.hdr files

disp(['ASLMRICloud: (' asl_paras.SINGLPROC.name_asl ') Calculate difference volume...']);

name_asl    = asl_paras.SINGLPROC.name_asl;
flag_multidelay = asl_paras.BASICPARA.flag_multidelay;
% labl_ordr   = asl_paras.BASICPARA.labl_ordr;

% Load scaled/realigned ASL data
if flag_multidelay == 0
    P = spm_select('FPList',path_temp,['^r' name_asl '.img$']);
else
    P = spm_select('FPList',path_temp,['^rr' name_asl '.img$']);
end
V = spm_vol(P);
img_all = spm_read_vols(V); img_all(isnan(img_all)) = 0;

% Calculate difference map
dyn = size(V,1);

% switch labl_ordr
%     case 'Control first'
%         ctrl = mean(img_all(:,:,:,1:2:dyn),4);
%         labl = mean(img_all(:,:,:,2:2:dyn),4);
%     case 'Label first'
%         ctrl = mean(img_all(:,:,:,2:2:dyn),4);
%         labl = mean(img_all(:,:,:,1:2:dyn),4);
% end

grp1 = mean(img_all(:,:,:,1:2:dyn),4);
grp2 = mean(img_all(:,:,:,2:2:dyn),4);
ordr = sign( mean(grp1(:)) - mean(grp2(:)) );
if ordr > 0
    ctrl = grp1;
    labl = grp2;
else
    ctrl = grp2;
    labl = grp1;
end

diff = ctrl - labl;

% Write averaged ctrl/labl/diff images to temp path
ovol        = V(1);
ovol.dt     = [16 0];
ovol1       = ovol;
ovol2       = ovol;
ovol3       = ovol;
ovol1.fname = strcat(path_temp,filesep,'r',name_asl,'_ctrl.img');
ovol2.fname = strcat(path_temp,filesep,'r',name_asl,'_labl.img');
ovol3.fname = strcat(path_temp,filesep,'r',name_asl,'_diff.img');
spm_write_vol(ovol1, ctrl);
spm_write_vol(ovol2, labl);
spm_write_vol(ovol3, diff);

