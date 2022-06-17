% Scripts for converting 3D image volumes into a 4D image
% May 1 2015
for sb =1:PAR.nsubs % for each subject
    str   = sprintf('sub #%3d/%3d: %-5s',sb,PAR.nsubs,PAR.subjects{sb} );
    fprintf('\r%-40s  %30s',str,' ')
    P=[];
    for c=1:PAR.ncond
        imgs=spm_select('FPList',PAR.condirs{sb,c},['^' PAR.confilters{c} '\w*\.img$']);
        if isempty(imgs)
            imgs=spm_select('FPList',PAR.condirs{sb,c},['^' PAR.confilters{c} '\w*\.nii$']);
            if size(imgs,1)>1
                fname=fullfile(PAR.condirs{sb,c}, [PAR.confilters{c} '_4D.nii']);
                spm_file_merge(imgs,fname);
            end
        else
            fname=fullfile(PAR.condirs{sb,c}, [PAR.confilters{c} '_4D.nii']);
            spm_file_merge(imgs,fname);
        end
    end
end
fprintf('\n');