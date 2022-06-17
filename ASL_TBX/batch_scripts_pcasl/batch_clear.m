% Delete intermediate files

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
    fprintf('%s%30s',repmat(sprintf('\b'),1,30),'...deleting intermediate files')  %-#
    %now get all images to reset orientation
    %prepare directory
    P=[];
    for c=1:PAR.ncond
        % get files in this directory
        %Ptmp=spm_select('FPList', char(PAR.condirs{sb,c}), ['^' PAR.confilters{c} '\w*\.img$']);
		cd(PAR.condirs{sb,c});	
        delete(['r*.hdr']);
        delete(['r*.img']);
        delete(['s*.hdr']);
        delete(['s*.img']);
        delete(['*flt_*.nii']);
    end
    cd(PAR.structdir{sb});
    % delete intermediate files for the anatomical folder
    fprintf('%s%30s',repmat(sprintf('\b'),1,30),'...done')  %-#
end
