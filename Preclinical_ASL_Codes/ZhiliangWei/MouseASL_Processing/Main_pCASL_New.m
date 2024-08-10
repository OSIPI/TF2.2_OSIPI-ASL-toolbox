clear all
clc
close all

% By Zhiliang Wei, August 12, 2016, JHSOM
% Modified on Dec. 24, 2021

% Reading in the last processing
fp=fopen('W_Filepath.txt');
filepath=fscanf(fp,'%s',1);
fclose(fp);
if exist(filepath)
    filepath=uigetdir(filepath);
else
    filepath=uigetdir();
end
% Store the filepath
fp=fopen('W_Filepath.txt','w');
fprintf(fp,'%s',filepath);
fclose(fp);

% Locate the pCASL scans
if exist([filepath filesep 'pCASL.txt'])
    expno=load([filepath filesep 'pCASL.txt']);
else
    expno=W_FindScan(filepath,'ASL')
    expno=[expno W_FindScan(filepath,'pcasl')]
    dlmwrite([filepath filesep 'pCASL.txt'],expno);
end
% Choose the dataset to process
for ni=1:length(expno)
    liststr{ni}=num2str(expno(ni));
end
[lists listv]=listdlg('PromptString','Select a dataset:',...
    'SelectionMode','Single',...
    'ListString',liststr);
expno=expno(lists);

% Directory to save data
[TempA TempB TempC]=fileparts(filepath);
savenum=load('W_Para.txt');
savedir=['Results' filesep 'pCASL_' num2str(savenum) '_' TempB '_' num2str(expno)];
dlmwrite('W_Para.txt',savenum+1);
if ~exist(savedir)
    mkdir(savedir);
end

% Parameter extractions
filename=[filepath filesep num2str(expno)];
Para=W_ImgParaAbs(filename);
Para.expno=expno;

% Exporting data
[Image NX NY NI]=read_2dseq_v3(filepath,expno,1);
ImageSize=size(Image);
W_ParaWrite([filepath filesep num2str(expno)],Para,0);
W_ParaWrite(savedir,Para,0);
save([savedir filesep 'Image.mat'],'Image');

% Check potential motion artefacts
if ImageSize(3)==1
    figure;imshow(mean(Image,4),[],'initialmag','fit');colorbar;
else
    SFF=floor(sqrt(ImageSize(3)));
    SFF1=ceil(ImageSize(3)./SFF);
    W_MSplot(sum(Image,4),[SFF SFF1],1,[]);colorbar;
end
title('Motion checking');
saveas(gcf,[savedir filesep 'MotionCheck'],'tif');

% Exclude the first few scans to ensure magnetization steady state 
ImageNew=Image(:,:,:,3:end);
ImageCtr=ImageNew(:,:,:,1:2:end);
ImageLab=ImageNew(:,:,:,2:2:end);
ImageDif=mean(ImageCtr-ImageLab,4);
if ImageSize(3)==1
    figure;imshow(ImageDif,[],'initialmag','fit');colorbar;
else
    W_MSplot(ImageDif,[SFF SFF1],1,[]);colorbar;
end
title('Difference images');
saveas(gcf,[savedir filesep 'ImageDif'],'tif');
save([savedir filesep 'ImageDif.mat'],'ImageDif');

% Display the M0 imagesc
M0Calib=(1-exp(-Para.tr/1900))
Mat0=mean(ImageCtr,4)./M0Calib;   % Calculate M0 from control
if ImageSize(3)==1
    figure;imshow(Mat0,[],'initialmag','fit');colorbar;
else
    W_MSplot(Mat0,[SFF SFF1],1,[]);colorbar;
end
title('M0 image');
saveas(gcf,[savedir filesep 'M0'],'tif');
save([savedir filesep 'Mat0.mat'],'Mat0');

% Gather the mask
if exist([Para.path filesep 'msmask.mat'])
    load([Para.path filesep 'msmask.mat']);
    save([savedir filesep 'msmask.mat'],'msmask');
else
    H=figure('name','ROI drawing ...');
    for ni=1:ImageSize(3)
        imshow(Mat0(:,:,ni),[],'initialmagnification','fit');
        title(['Slice # ' num2str(ni)]);
        msmask(:,:,ni)=roipoly;
    end
    save([Para.path filesep 'msmask.mat'],'msmask');
    save([savedir filesep 'msmask.mat'],'msmask');
    close(H);
end

% Calculate the CBF images
relCBF=abs(ImageDif)./Mat0.*msmask*100;
% relCBF=abs(ImageDif)./Mat0.*100;
Mat0=Mat0.*msmask;

% Adjust the display range
if exist([Para.path filesep 'DisRange.txt'])
    Range=load([Para.path filesep 'DisRange.txt']);
    x1=Range(1);x2=Range(2);
    y1=Range(3);y2=Range(4);
    dlmwrite([savedir filesep 'DisRange.txt'],Range);
else
    H=figure('name','CBF Map Cutter');
    imagesc(sum(relCBF,3));
    [y1 x1 keyvalue]=ginput(1);
    [y2 x2 keyvalue]=ginput(1);
    x1=fix(x1);x2=fix(x2);
    y1=fix(y1);y2=fix(y2);
    close(H);
    dlmwrite([Para.path filesep 'DisRange.txt'],[x1 x2 y1 y2]);
    dlmwrite([savedir filesep 'DisRange.txt'],[x1 x2 y1 y2]);
end

% Display the perfusion map
if ImageSize(3)==1
    figure;imshow(relCBF,[0 8],'initialmag','fit');colorbar;
else
    W_MSplot(relCBF,[SFF SFF1],1,[0 8]);colorbar;
end
title('Relative CBF (%)');
saveas(gcf,[savedir filesep 'RelCBF'],'tif');

% Delay-time calibration for multislice acquisitions
if ImageSize(3)>1
    SGap=31;        % unit:ms; the delay between two adjacent EPI Acq.
    T1blood=2800;    % unit:ms; 
    if mod(Para.slicenum,2)==1
        AdjList=[1:floor(Para.slicenum/2);...
            Para.slicenum-floor(Para.slicenum/2)+1:Para.slicenum];
        AdjList=AdjList(:);
        AdjList(Para.slicenum)=ceil(Para.slicenum/2);
    else
        AdjList=[1:Para.slicenum/2;...
            Para.slicenum/2+1:Para.slicenum];
        AdjList=AdjList(:);
    end
    AdjList=SGap.*(AdjList-1);
    AdjF=exp(AdjList./T1blood);
    disp('Across-slice PLD correction:');
    disp(num2str(AdjF));
    % Rescale the slices
    for ni=1:ImageSize(3)
        relCBF(:,:,ni)=AdjF(ni).*relCBF(:,:,ni);
    end

%     % Cross-talk effect calibration for multislice acquisitions
%     for ni=1:ImageSize(3)       % Before calibration
%         temp_cbf_val(1,ni)=sum(sum(relCBF(:,:,ni).*msmask(:,:,ni)))./sum(sum(msmask(:,:,ni)));
%     end
%     relCBF_odd=relCBF(:,:,1:2:end);
%     relCBF_odd=relCBF_odd(:);
%     relCBF_even=relCBF(:,:,2:2:end);
%     relCBF_even=relCBF_even(:);
%     figure;
%     subplot(2,1,1);
%     h_odd=histogram(relCBF_odd);
%     set(h_odd,'BinLimits',[0.01 10]);
%     res_odd=W_Normal(0.5*(h_odd.BinEdges(1:end-1)+h_odd.BinEdges(2:end)),h_odd.Values);
%     hold on;plot(0.5*(h_odd.BinEdges(1:end-1)+h_odd.BinEdges(2:end)),res_odd.val,'r-');
%     title('Odd slices');
%     subplot(2,1,2);
%     h_even=histogram(relCBF_even);
%     set(h_even,'BinLimits',[0.01 10]);
%     res_even=W_Normal(0.5*(h_even.BinEdges(1:end-1)+h_even.BinEdges(2:end)),h_even.Values);
%     hold on;plot(0.5*(h_even.BinEdges(1:end-1)+h_even.BinEdges(2:end)),res_even.val,'r-');
%     title('Even slices');
%     temp_cbf_scale=res_odd.beta(2)./res_even.beta(2)
%     relCBF(:,:,2:2:end)=temp_cbf_scale.*relCBF(:,:,2:2:end); 
%     for ni=1:ImageSize(3)       % After calibration
%         temp_cbf_val(2,ni)=sum(sum(relCBF(:,:,ni).*msmask(:,:,ni)))./sum(sum(msmask(:,:,ni)));
%     end
    save([savedir filesep 'relCBF.mat'],'relCBF');
%     figure('position',[200 200 800 400]);
%     plot(temp_cbf_val(1,:),'b*--');
%     hold on;
%     plot(temp_cbf_val(2,:),'ro--');
%     legend('Pre-','Post-');
%     ylim([2 8]);
%     xlabel('Slice Num');
%     ylabel('Relative CBF (%)');
%     W_Plot;
%     saveas(gcf,[savedir filesep 'CalibCBF'],'tif');
else
    disp('Inter-slice-PLD correction not required ...');
    disp('Cross-talk correction not required ...');
end

% Combine the submatrices
if ImageSize(3)==1
    grelCBF=relCBF;
    gMat0=Mat0;
else
    grelCBF=W_MSplot(relCBF(x1:x2,y1:y2,:),[SFF SFF1],0,[0 10]);
    gMat0=W_MSplot(Mat0(x1:x2,y1:y2,:).*msmask(x1:x2,y1:y2,:),[SFF SFF1],0,[]);
end
figure('position',[200 200 fliplr(size(grelCBF))]);
imshow(grelCBF,[0 8],'initialmag','fit','border','tight');axis normal;
title('Packed CBF');
saveas(gcf,[savedir filesep 'PackedCBF'],'tif');
save([savedir filesep 'grelCBF.mat'],'grelCBF');
figure('position',[200 200 fliplr(size(grelCBF))]);
imshow(gMat0,[0 80],'initialmag','fit','border','tight');axis normal;
title('Packed M0');
saveas(gcf,[savedir filesep 'PackedM0'],'tif');
save([savedir filesep 'gMat0.mat'],'gMat0');

aslave=sum(sum(sum(relCBF.*msmask)))./sum(sum(sum(msmask)));
disp(['The averaged ASL signal is: ' num2str(aslave) '%']);

figure;imshow(grelCBF,[0 10],'initialmag','fit');colorbar;colormap(hot);











