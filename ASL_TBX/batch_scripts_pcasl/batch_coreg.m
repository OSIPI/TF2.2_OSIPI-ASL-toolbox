% SPM2 batch file to do coregistration
% !!!!!(of structural to mean)


disp('Coregistration between structural images and the functional images for all subjects, it takes a while....');
global defaults;
spm_defaults;
flags = defaults.coreg;

% dirnames,
% get the subdirectories in the main directory
for s = 1:length(PAR.subjects) % for each subject
    %take the dir where the mean image (reslice) is stored (only first condition)
    sprintf('\nNow coregister %s''s data\n',char(PAR.subjects{s}))
    dir_fun = PAR.condirs{s,1};
    %take the structural directory
    dir_anat = PAR.structdir{s};
    % get mean in this directory
    %target - Tar(G)et image, NEVER CHANGED
    %source - Source image, transformed to match PG
    %otherimgs - (O)ther images, originally realigned to PF and transformed again to PF

    target = spm_select('FPList',PAR.structdir{s},['^' PAR.structprefs '\w*\.nii$']);
    source = spm_select('FPList', dir_fun,   ['^mean' PAR.funcimgfilters{1} '\w*\.nii$']);
    PO=[];
    for c=1:PAR.ncond
        % get files in this directory
       % Ptmp=spm_get('files', PAR.condirs{s,c}, ['r*img']);
        Ptmp=spm_select('EXTFPList', char(PAR.condirs{s,c}), ['^r' PAR.funcimgfilters{c} '.*\.nii'], 1:400);
        PO=strvcat(PO,Ptmp);
    end
    if isempty(PO) | PO=='/'
        PO=source;
    else
        PO = strvcat(source,PO);
    end
    otherimgs = PO;
    ASLtbx_spmcoreg(target, source, PO);
end
