function output = ASLSmoothImage(data, spatialdim, FWHM, voxelsize)
% ASL Script, Siero 2019 - 01-03-2019
% Smooth the ASL images with MATLAB function: imgaussfilt3 or imgaussfilt


%FWHM=sigma*2.355;
sigma=FWHM/2.355;
inplanevoxelsize=voxelsize(1);
data_smooth=zeros(size(data));
if spatialdim==2
    for s=1:size(data, 3)
        if ~isempty(isnan(data))
            filtWidth = 7;
            filtSigma = sigma/inplanevoxelsize;
            imageFilter=fspecial('gaussian',filtWidth,filtSigma);
            data_smooth(:,:,s)= nanconv(data(:,:,s),imageFilter, 'nanout');
        else
            data_smooth(:,:,s)=imgaussfilt(data(:,:,s),sigma/inplanevoxelsize, 'FilterDomain', 'spatial'); % here also fitler width of 7 is used internally
        end
    end
    
elseif spatialdim==3
    if isnan(data)
        error(' NANs found, not supported yet!, will eat away the data at the edges, use 2D smoothing instead for now....')
    else
        data_smooth=imgaussfilt3(data,sigma./voxelsize, 'FilterDomain', 'spatial');
        
    end
end


output=double(data_smooth);
