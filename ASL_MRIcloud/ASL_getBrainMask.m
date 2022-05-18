function [brnmsk_dspl, brnmsk_clcu] = ASL_getBrainMask(imgtpm,imgfile,flag_addrealignmsk)
% generate brain mask:
%   if fov is too thin or less slices, use slice-by-slice threshold-based
%   method; otherwise, use spm segmentation-based method.
% output:
%   brnmsk_dspl (datatype, logical), used for cbf map display;
%   brnmsk_clcu (datatype, logical), used for glo_cbf calculation.
% yli20160615

[imgpath,imgfn,ext] = fileparts(imgfile);
P = spm_select('FPList',imgpath,['^' imgfn '\' ext]);
V = spm_vol(P);
imgvol = spm_read_vols(V); imgvol(isnan(imgvol)) = 0;

matsize = V(1).dim;
voxsize = abs(V(1).mat(eye(4,3)==1))';
fov     = matsize.*voxsize;

% if any dimension is less than 80mm, or slice number is less than 9, 
% it is small fov. Segmentation method probably will not work.
flag_small_fov = (sum(fov<80) > 0) || (sum(matsize<9) > 0);

% load mask from realignment and apply to final brain mask
P1 = spm_select('FPList',imgpath,['.*brnmsk_realign.img$']);
if ~isempty(P1) && flag_addrealignmsk
    P1 = spm_vol(P1);
    V1 = spm_read_vols(P1);
    brnmsk_realign = V1 > 0.5;
else
    brnmsk_realign = (ones(matsize) > 0.5);
end


switch flag_small_fov
    case 0 % segmentation-based method
        % initiate spm_jobman
        spm('defaults','fmri'); spm_jobman('initcfg');
        matlabbatch = [];
        
        ngaus  = [1 1 2 3 4 2];
        native = [1 1 1 0 0 0];
        for ii = 1:6
            matlabbatch{1}.spm.spatial.preproc.tissue(ii).tpm = {[imgtpm ',' num2str(ii)]};
            matlabbatch{1}.spm.spatial.preproc.tissue(ii).ngaus = ngaus(ii);
            matlabbatch{1}.spm.spatial.preproc.tissue(ii).native = [native(ii) 0];
            matlabbatch{1}.spm.spatial.preproc.tissue(ii).warped = [0 0];
        end
        
        matlabbatch{1}.spm.spatial.preproc.channel.vols = {[imgfile ',1']};
        matlabbatch{1}.spm.spatial.preproc.channel.biasreg = 0.001;
        matlabbatch{1}.spm.spatial.preproc.channel.biasfwhm = 60;
        matlabbatch{1}.spm.spatial.preproc.channel.write = [0 0];
        matlabbatch{1}.spm.spatial.preproc.warp.mrf = 1;
        matlabbatch{1}.spm.spatial.preproc.warp.cleanup = 1;
        matlabbatch{1}.spm.spatial.preproc.warp.reg = [0 0.001 0.5 0.05 0.2];
        matlabbatch{1}.spm.spatial.preproc.warp.affreg = 'mni';
        matlabbatch{1}.spm.spatial.preproc.warp.fwhm = 0;
        matlabbatch{1}.spm.spatial.preproc.warp.samp = 3;
        matlabbatch{1}.spm.spatial.preproc.warp.write = [0 0];
        
        spm_jobman('run',matlabbatch);
        
        % add GM WM CSF masks together to get brain mask
        [imgpath,~,~] = fileparts(imgfile);
        P = spm_select('FPList',imgpath,['^c.*' imgfn '.*.nii$']);
        V = spm_vol(P(1:3,:));
        mvol = spm_read_vols(V);
        mask = sum(mvol,4);
        
        mask = mask > 0.5;
        for ss = 1:size(mask,3)
            slice = mask(:,:,ss);
            mask(:,:,ss) = imfill(slice,'holes');
        end
        
        % erode or dilate to generate masks
        [xx,yy,zz]  = ndgrid(-1:1);
        se          = sqrt(xx.^2 + yy.^2 + zz.^2) <= 1;
        mask1       = imerode(mask,se); % erode by 1 layer
        mask2       = imdilate(mask,se); % dilate by 1 layer
        brnmsk_clcu = logical(mask1 .* brnmsk_realign);
        % brnmsk_dspl = logical(mask2);
        brnmsk_dspl = logical(mask  .* brnmsk_realign); % no-dilate mask for display
        
    case 1
        % if thin slab or less slices, threshold slice by slice
        thre = 0.5;  % vox > thre * mean(center_part)
        mask1 = inbrain(imgvol,thre,2,1); % erode by 1 layer
        mask2 = inbrain(imgvol,thre,2,2); % dilate by 1 layer -> no dilate
        brnmsk_clcu = logical(mask1 .* uint8(brnmsk_realign));
        brnmsk_dspl = logical(mask2 .* uint8(brnmsk_realign));
end
end


function brainmask = inbrain(imgvol,thre,ero_lyr,dlt_lyr)
% generate in-brain voxels
lowb  = 0.25;
highb = 0.75;

% get the threshold value and threshold
[Nx,Ny,Nz] = size(imgvol);
tmpmat = imgvol(max(1,round(Nx*lowb)):min(Nx,round(Nx*highb)),...
                max(1,round(Ny*lowb)):min(Ny,round(Ny*highb)),...
                max(1,round(Nz*lowb)):min(Nz,round(Nz*highb)));
tmpvox = tmpmat(tmpmat>0);
thre0  = mean(tmpvox(:))*thre;

mask1  = zeros(size(imgvol));
mask1(imgvol > thre0) = 1;

% erode, find largest cluster, fill holes, dilate for each slice
mask2 = zeros(size(mask1));
for ii = 1:Nz
    % get the slice
    slice0 = mask1(:,:,ii);
    % erode
    se     = [0 1 0; 1 1 1; 0 1 0];
    slice1 = slice0;
    for ie = 1:ero_lyr
        slice1 = imerode(slice1,se);
    end
    % find largest cluster
    CC     = bwconncomp(slice1,4);
    npx    = cellfun(@numel,CC.PixelIdxList);
    [~,idx] = max(npx);
    slice2 = zeros(size(slice0));
    slice2(CC.PixelIdxList{idx}) = 1;
    % fill holes
    slice2  = imfill(slice2,'holes');
    % dilate
    for id = 1:dlt_lyr
        slice2  = imdilate(slice2,se);
    end
    
    mask2(:,:,ii) = slice2;
end

brainmask = uint8(mask2);
end

