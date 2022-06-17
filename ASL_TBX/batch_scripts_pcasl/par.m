% Batch mode scripts for running spm5 in TRC
% Created by Ze Wang, 08-05-2004
% zewang@mail.med.upenn.edu


fprintf('\r%s\n',repmat(sprintf('-'),1,30))
fprintf('%-40s\n','Set PAR')


clear
global PAR
PAR=[];


PAR.SPM_path=spm('Dir');
addpath(PAR.SPM_path);

% This file sets up various things specific to this
% analysis, and stores them in the global variable PAR,
% which is used by the other batch files.
% You don't have to do it this way of course, I just
% found it easier



%%%%%%%%%%%%%%%%%%%%%
%                   %
%   GENERAL PREFS   %
%                   %
%%%%%%%%%%%%%%%%%%%%%%
% Where the subjects' data directories are stored

PAR.batchcode_which= mfilename('fullpath');
PAR.batchcode_which=fileparts(PAR.batchcode_which);
addpath(PAR.batchcode_which);
old_pwd=pwd;
cd(PAR.batchcode_which);
cd ../
data_root=pwd;
cd(old_pwd);


PAR.root=data_root;

% Subjects' directories
PAR.subjects = {'sub1' 'sub2' } ;
PAR.nsubs = length(PAR.subjects);



% Anatomical directory name
PAR.structfilter='STRUC';

PAR.structprefs = 'T1';
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Get the anatomical image directories automatically
for sb=1:PAR.nsubs
    tmp=dir(fullfile(PAR.root,PAR.subjects{sb},['*' PAR.structfilter '*']));
    if size(tmp,1)==0
        sprintf('Can not find the anatomical directory for subject\n')
        sprintf('%s: \n', char(PAR.subjects{sb}))
        error('Can not find the anatomical directory for subject');
    end
    if size(tmp,1)>1
        sprintf('More than 1 anatomical directories for subject: %s are found here!\n',char(PAR.subjects{sb}))
        error('More than 1 anatomical directories are found')
    end
    PAR.structdir{sb}=fullfile(PAR.root,PAR.subjects{sb},spm_str_manip(char(tmp(1).name),'d'));
end
%prefixes for filenames of structural 3D images, supposed to be the same for every subj.

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
% Getting condition directories
PAR.sessionfilters={'FUNC'};   % ASL image folder
PAR.sessionM0filters={'FUNC'};

PAR.ncond=length(PAR.sessionfilters);
PAR.funcimgfilters={'ASL'}; % ASL image name
PAR.M0filters = {'M0'};     % M0 image name
% The condition names are assumed same for different sessions

for sb=1:PAR.nsubs
    for c=1:PAR.ncond
        tmp=dir(fullfile(PAR.root,PAR.subjects{sb},['*' PAR.sessionfilters{c} '*']));

        if size(tmp,1)==0
            sprintf('Can not find the condition directory for subject\n')
            sprintf('%s: \n', char(PAR.subjects{sb}))
            error('Can not find the condition directory for subject');
        end

        if size(tmp,1)>1
            sprintf('Panic! subject %s has more than 1 directories!\n', [PAR.subjects{sb}])
            error('Panic! condition has more than 1 directories!')
            %return;
        end
        PAR.condirs{sb,c}=fullfile(PAR.root,PAR.subjects{sb},spm_str_manip(char(tmp(1).name),'d'));
        PAR.M0dirs{sb,c}=fullfile(PAR.root,PAR.subjects{sb},spm_str_manip(char(tmp(1).name),'d'));
    end
end

% Smoothing kernel size
PAR.FWHM = [6];
PAR.bb   = [-90 -126 -72;  90    90  108];%[-78 -112 -70; 78 76 85];
% % TR for each subject.  As one experiment was carried out in one Hospital (with one machine)
% % and the other in another hospital (different machine), TRs are slightly different
% %PAR.TRs = [2.4696 2];
PAR.TRs = ones(1,PAR.nsubs)*6;
% PAR.mp='no';

%
PAR.mp='no';
%
PAR.groupdir = ['STAT'];

PAR.ana_dir = ['glm'];
PAR.subtractiontype=0;
PAR.glcbffile=['globalsg_' num2str(PAR.subtractiontype) '.txt'];
PAR.img4analysis='cbf'; % or 'Perf'
PAR.ana_dir = ['glm_' PAR.img4analysis];
PAR.Filter='cbf_0_sr';
% parameters for cbf quantification
PAR.FirstimageType=0;       % 0 means labeling first (images are acquired in an order of label control label ...
PAR.SubtractionType=0;      % 0: simple subtraction, 1: surround subtraction, 2: sinc subtraction
PAR.SubtractionOrder=1;     % 0: label - control, 1: control - label
PAR.MaskFlag=1;    % Flag #1, 1 means masking out images using an implicit or explicit mask image
PAR.MeanFlag=1;    % Flag #2, 1 means creating mean images (for the non-subtracted raw data, ASL CBF images, or the perfusion difference images
PAR.CBFFlag=1;     % Flag #3, 1 means calculating CBF (this is the default value)
PAR.BOLDFlag=0;    % Flag #4, 1 means extracting pseudo BOLD images (an obsolete option)
PAR.OutPerfFlag=0; % Flag #5, 1 means saving the perfusion difference images (the perfusion weighted images)
PAR.OutCBFFlag=1;  % Flag #6, 1 means saving CBF images rather than only the mean CBF map if MeanFlag is on
PAR.QuantFlag=0;   % Flag #7, 1 means using a unique M0 value for the whole brain during CBF calculation
PAR.ImgformatFlag=1;  % Flag #8, 1 means saving images in NifTI format
PAR.D4Flag=1;      % Flag #9, 1 means saving the image series in 4D format
PAR.M0wmcsfFlag=0; % Flag #10, 1 means using M0csf to estimate M0b, 0 means using M0wm
PAR.Flags=[PAR.MaskFlag   PAR.MeanFlag  PAR.CBFFlag       PAR.BOLDFlag PAR.OutPerfFlag ...
           PAR.OutCBFFlag PAR.QuantFlag PAR.ImgformatFlag PAR.D4Flag   PAR.M0wmcsfFlag];
PAR.TimeShift = 0.5; %  time shift for sinc interpolation. 0.5 means moving half of TR
PAR.ASLType  = 1;    % 1 means CASL or PCASL, 0 means PASL
PAR.Labeff   = 0.85;  % label efficiency. 0.85 for pcasl, 0.9 for pasl
PAR.MagType  = 1;    % 1 means 3T   (please read the header in asl_perf_subtrac.m for more details
PAR.Labeltime = 1.48; % labeling time in secs. For PASL, this parameter is for passing the TI1. If it is >1, this value will be disabled.
PAR.Delaytime = 1.5; % post labeling delay time. For QUIPSS, this should be set to TI2-TI1. 
PAR.slicetime = 33.5;   % slice acquisition time in msec.  Refer to the manual for how to calculate it.
PAR.TE = 11;         % in msecs
PAR.additionalM0 = 0;   % 0 means no. In CASL pCASL, if additional M0 is acquired, you can use it, otherwise the control image will be used.
                        % 1 means using additional M0 map. The M0 map should be saved in the same folder as in the ASL rawdata and should be named by "M0.nii"


