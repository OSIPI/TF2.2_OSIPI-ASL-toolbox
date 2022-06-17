% batch reset T1 orientation

global PAR
par
fprintf('\r%-40s\n','batch reset orientation ')
%%%%% the following codes are changed from batch_smooth

% dirnames,
% get the subdirectories in the main directory
for sb = 1:PAR.nsubs % for each subject
    %go get the sessions
    str   = sprintf('sub #%3d/%3d: %-5s',sb,PAR.nsubs,PAR.subjects{sb} );
    fprintf('\r%-40s  %30s',str,' ')
    fprintf('%s%30s',repmat(sprintf('\b'),1,30),'...reseting')  %-#
    %now get all images to reset orientation
    %prepare directory
    P=[];
    for c=1:PAR.ncond
        % get files in this directory
        P=spm_select('FPList', char(PAR.condirs{sb,c}), ['^' PAR.funcimgfilters{c} '.*\.nii$']);
%         ASLtbx_resetimgorgASL(P);
        ASLtbx_resetimgorg(P);
    end

    P=spm_select('FPList', char(PAR.structdir{sb}), ['^' PAR.structprefs '.*\.nii$']);
    ASLtbx_resetimgorg(P);
    
    fprintf('%s%30s',repmat(sprintf('\b'),1,30),'...done')  %-#
end
fprintf('\n');
