function [output, output_nantmean, NANCOUNTMASK] = ASLQuantificationPCASL(data, M0, pld, tau,T1blood, lambda, alpha,slicecorr,slicetime,echotime, CBF_scale, mask, outlierthreshold, showfigure)
%% ASL Quantification Script, Siero 2019 - 01-03-2019
% Based on Alsop et al MRM 2014, ASl White paper
% Calculate the CBF using M0 map
% 'data' is the subtraction data at TI=xx second.
% the unit of CBF is ml/100g/min
% 6000 to convert to 100gr/ml/min
% pld = post-label-delay in s
% tau = label duration in s
% T1blood = T1 arterial blood water (in s)
% lambda = water partition fraction
% alpha = label efficiency
% slicecorr, 'yes' (do slicetime correction, i.e. change PLD per slice), 'no' (no slice timecorrection), 'already', (slicetim correciton has already been on on the data)
% slicetime, (in ms) time it takes to scan 1 slice
% echotime (in ms), only used for slice time correction
% M0=M0*T2star_corr/lambda;% conversion from total M0 to blood M0
% CBF_scale, intensity difference (i.e. echotime differences between M0 and
% ASL images, can be set as 1 when no echotime difference exists between M0
% and the ASL images
% mask is a whole brain logical mask
% outlierthershold, set to 'yes' to remove outliers (default 3 times the 1.428MAD)

%% Example 
% [output, output_nantmean, NANCOUNTMASK] = ASLQuantificationPCASL(data, M0, 1.8, 1.8,1.6, 0.9, 0.6,'no','',14, 1, mask, 'yes', 'yesfigure');
data=double(data)*CBF_scale;
CBF = zeros(size(data));
M0=double(M0);
if size(data,4) == 1
    if strcmp(slicecorr,'yes')
        disp(['Performing slice time correction in CBF quantification'])
        nslices=size(data,3);
        pld_sc= [pld + echotime/1000,pld + echotime/1000 + slicetime/1000*[1:nslices-1]];
        nslices=size(data,3);
        for i=1:nslices
            CBF(:,:,i) = 6000*data(:,:,i)*lambda*exp(pld_sc(i)/T1blood)./((2*alpha.*T1blood*M0(:,:,i))*(1-exp(-tau/T1blood)));
        end
    elseif strcmp(slicecorr,'already')
        disp(['Slice time correction for slice-dependent PLD already performed! Skipping PLD in quantification...'])
        CBF = 6000*data*lambda./((2*alpha.*T1blood*M0)*(1-exp(-tau/T1blood)));
    elseif strcmp(slicecorr,'no')
        disp(['Skipping slice time correction in CBF quantification '])
        CBF = 6000*data*lambda.*exp(pld/T1blood)./((2*alpha.*T1blood.*M0).*(1-exp(-tau/T1blood)));
    end
    
    CBF(isinf(abs(CBF)))=NaN;  % consider these NaN,
    
    if strcmp(outlierthreshold,'yes')
        factor=3;
        CBFoutlier1=median(CBF(mask)) + mad(CBF(mask))*3*1.428; % median absolute deviation *1.428 equals the corresponding stdev (from normal distribution)
        CBFoutlier2=median(CBF(mask)) - mad(CBF(mask))*3*1.428; % median absolute deviation *1.428 equals the corresponding stdev (from normal distribution)
        
        CBF(CBF>CBFoutlier1)=NaN;
        CBF(CBF<CBFoutlier2)=NaN;
    end
    
else
    ndyns=size(data,4);
    if strcmp(slicecorr,'yes')
        disp(['Performing slice time correction in CBF quantification '])
        nslices=size(data,3);
        pld_sc= [pld + echotime/1000,pld + echotime/1000 + slicetime/1000*[1:nslices-1]];
        nslices=size(data,3);
        for d=1:ndyns
            for i=1:nslices
                CBF(:,:,i,d) = 6000*data(:,:,i,d)*lambda*exp(pld_sc(i)/T1blood)./((2*alpha.*T1blood*M0(:,:,i))*(1-exp(-tau/T1blood)));
            end
        end
    elseif strcmp(slicecorr,'already')
        disp(['Slice time correction for slice-dependent PLD already performed! Skipping PLD in quantification...'])
        for d=1:ndyns
            CBF(:,:,:,d) = 6000*data(:,:,:,d)*lambda./((2*alpha.*T1blood*M0)*(1-exp(-tau/T1blood)));
        end
    elseif strcmp(slicecorr,'no')
        disp(['Skipping slice time correction in CBF quantification '])
        for d=1:ndyns
            CBF(:,:,:,d)= 6000*data(:,:,:,d)*lambda.*exp(pld/T1blood)./((2*alpha.*T1blood.*M0).*(1-exp(-tau/T1blood)));
        end
    end
    CBF(isinf(abs(CBF)))=NaN;  % consider these NaN,
    CBF_nantmean=nanmean(double(CBF),4);
    if strcmp(outlierthreshold,'yes')
        factor=3;
        CBFoutlier1=median(CBF_nantmean(mask)) + mad(CBF_nantmean(mask))*3*1.428; % median absolute deviation *1.428 equals the corresponding stdev (from normal distribution)
        CBFoutlier2=median(CBF_nantmean(mask)) - mad(CBF_nantmean(mask))*3*1.428; % median absolute deviation *1.428 equals the corresponding stdev (from normal distribution)
        
        CBF_nantmean(CBF_nantmean>CBFoutlier1)=NaN;
        CBF_nantmean(CBF_nantmean<CBFoutlier2)=NaN;
        
    end
end

% look for NANS and make mask
NANCOUNT=zeros(size(data));
for i=1:size(data,1)
    for j=1:size(data,2)
        for k=1:size(data,3)
            NANCOUNT(i,j,k)=numel(find( isnan(CBF(i,j,k,:))));
        end
    end
end
NANCOUNTMASK=NANCOUNT.*mask;
NANMASK=NANCOUNTMASK+NANCOUNT;
% check where these NANs end up, especially for timeseries CBF quantification
if strcmp(showfigure,'yesfigure')
    figure,
%     subplot 121, mmontage(NANMASK); title('NaN map in mask'),
%     subplot 122, mmontage(nanmean(CBF,4));caxis([0 100]), colormap gray; title(' CBF map, [0 100]'),freezeColors,
    subplot 121, montage(NANMASK); title('NaN map in mask'),
    subplot 122, montage(nanmean(CBF,4));caxis([0 100]), colormap gray; title(' CBF map, [0 100]');%LZ
end

% output data
output=CBF;
if size(data,4) == 1
    output_nantmean = [];
else
    output_nantmean = CBF_nantmean;
end

