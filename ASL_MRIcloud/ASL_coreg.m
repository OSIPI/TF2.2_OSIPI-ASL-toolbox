function ASL_coreg(target,source,varargin)
% coregister source to target and apply transform matrix to source and 
% varargin
% dependent package - spm12

spm('defaults','fmri'); spm_jobman('initcfg');

coregparas = struct();

coregparas.ref = {target};
coregparas.source = {[source ',1']};
if nargin > 2
    coregparas.other = [{[source ',1']}, strcat(varargin,',1')]'; % n*1 cell
else 
    coregparas.other = [{[source ',1']}];
end
coregparas.eoptions.cost_fun = 'nmi';
coregparas.eoptions.sep = [4 2];
coregparas.eoptions.tol = [0.02 0.02 0.02 0.001 0.001 0.001 0.01 0.01 0.01 0.001 0.001 0.001];
coregparas.eoptions.fwhm = [7 7];
coregparas.roptions.interp = 1; % trilinear
coregparas.roptions.wrap = [0 0 0];
coregparas.roptions.mask = 0;
coregparas.roptions.prefix = 'r';

matlabbatch = [];
matlabbatch{1}.spm.spatial.coreg.estwrite = coregparas;
spm_jobman('run',matlabbatch);
