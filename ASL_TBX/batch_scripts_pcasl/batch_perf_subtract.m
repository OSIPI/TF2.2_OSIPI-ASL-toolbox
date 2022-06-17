% Toolbox for batch processing ASL perfusion based fMRI data.
% All rights reserved.
% Ze Wang @ TRC, CFN, Upenn 2004
%
% Batch calculation for the perfusion signals.

for sb = 1:PAR.nsubs % for each subject

    sprintf('Calculate perfusion and CBF signals for subject #%g ... %g subjects left...',sb,length(PAR.subjects)-sb)
    for c=1:PAR.ncond

        P=[];
        %ptmp=spm_get('files', PAR.condirs{s,1}, [PAR.subjects{s} '*' PAR.confilters{1} '*img']);
        %P=ptmp(1,:);
        % creating a mask image for removing background
        maskimg = spm_select('FPList', PAR.condirs{sb,c},    ['^brainmask_nat\w*\.nii$']);
        P =  spm_select('ExtFPList', PAR.condirs{sb,c}, ['^sASLflt.*\.nii'], 1:1000 );
        if PAR.additionalM0==0 
            M0img=[];
        else
            M0img = spm_select('FPList', PAR.M0dirs{sb,c}, ['^s' PAR.M0filters '.*\.nii']);
            if isempty(M0img)
                M0img = spm_select('FPList', PAR.M0dirs{sb,c}, ['^' PAR.M0filters '.*\.nii']);
            end
        end
        %        spm_perf_subtract(Filename,FirstimageType, SubtractionType,...
        %           SubtractionOrder,Flag,Timeshift,AslType,MagType,Labeltime,Delaytime,Slicetime,M0img,M0seg,maskimg)
        asl_perf_subtract(P, PAR.FirstimageType, PAR.SubtractionType, ...
            PAR.SubtractionOrder,   PAR.Flags,...
            PAR.TimeShift,     PAR.ASLType,      PAR.Labeff, PAR.MagType,...
            PAR.Labeltime,     PAR.Delaytime,    PAR.slicetime, PAR.TE,   M0img, [], maskimg);
        
        % labeling time=1.48s, post labeling delay=1.5 s, slice time=33.5
        % msec, TE=11 msec, no explicit M0 image, no mask for extracting M0
        % value (like M0 white matter etc) provided.
        
    end
end

