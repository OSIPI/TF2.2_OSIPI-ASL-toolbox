% Toolbox for batch processing ASL perfusion based fMRI data.
% All rights reserved.
% Ze Wang @ TRC, CFN, Upenn 2004
%
%
% Smoothing batch file for SPM2

% Get subject etc parameters
disp('Smoothing the realigned functional images, it is quick....');
org_pwd=pwd;
% dirnames,
% get the subdirectories in the main directory
for sb = 1:PAR.nsubs % for each subject

    str   = sprintf('sub #%3d/%3d: %-5s',sb,PAR.nsubs,PAR.subjects{sb});
    fprintf('\r%-40s  %30s',str,' ')
    fprintf('%s%30s',repmat(sprintf('\b'),1,30),'...smoothing')  %-#

    for c=1:PAR.ncond
        %P=[];
        %dir_func = fullfile(PAR.root, PAR.subjects{s},PAR.sesses{ses},PAR.condirs{c});
        
              
        fltimgs=spm_select('FPList', PAR.condirs{sb,c}, '^ASLflt.*nii'); 
        
        if PAR.additionalM0==1 
            M0img = spm_select('FPList', PAR.M0dirs{sb,c}, ['^' PAR.M0filters '.*\.nii']);
            if isempty(M0img), continue; end
            fltimgs=strvcat(fltimgs, M0img);
        end
        if isempty(fltimgs), fprintf('You didn''t selecte any images!\n'); return;end;
        if size(fltimgs,1)==1
            [pth,nam,ext,num] = spm_fileparts(fltimgs);
            fltimgs=fullfile(pth, [nam ext]);
        end
        [pth,nam,ext,num] = spm_fileparts(fltimgs(1,:));
         ASLtbx_smoothing(fltimgs, PAR.FWHM);
        
       
    end

end
cd(org_pwd);
