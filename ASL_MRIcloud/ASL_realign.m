function P = ASL_realign(path_temp, name_asl)
% Motion correction

disp(['ASLMRICloud: (' name_asl ') Realign ASL data...']);

% Get image files
P = spm_select('FPList',path_temp,['^' name_asl '.*\.img']);
V = spm_vol(P);

defaults = spm_get_defaults;
FlagsC = struct('quality',defaults.realign.estimate.quality,'fwhm',5,'rtm',0);
spm_realign(V, FlagsC);

which_writerealign = 2;
mean_writerealign  = 1;
FlagsR = struct('interp',defaults.realign.write.interp,...
    'wrap',defaults.realign.write.wrap,...
    'mask',true,... % mask in case invalid value in ROI analysis
    'which',which_writerealign,'mean',mean_writerealign);
%     'mask',defaults.realign.write.mask,...
spm_reslice_yli(P,FlagsR);

% % export mask from realignment
% rP = spm_select('FPList',path_temp,['^r' name_asl '.img$']);
% rP = spm_vol(rP);
% rV = spm_read_vols(rP);
% brnmsk_realign = isfinite(mean(rV,4)); % figure, imshow(tilepages(brnmsk_realign));
% 
% oP = rP(1);
% oP.fname = [path_temp filesep 'r' name_asl '_brnmsk_realign.img'];
% oP.pinfo = [1;0;0];
% oP.dt    = [4 0];
% spm_write_vol(oP,brnmsk_realign);

