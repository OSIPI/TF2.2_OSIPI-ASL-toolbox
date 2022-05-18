function [output, Iremoved_array ]= ASLOutlierRemoval(data, brainmask, GMmask, WMmask, CSFmask)
%% ASL OutlierRemoval (volumes), Siero 2019 - 01-03-2019
%method by Duloi et al JMRI 2017
%deals with NaN, and deltaM as data input
%data will be ASL difference in 4D (x,y,z，CTRL-TAG）


normfactor=mean(data(brainmask));
data=data/normfactor; %normalize to hanndle the noramlly very  high signal values (floats) on delta M images


%confine to brain tissue voxels
GMmask = logical(GMmask.*brainmask); 
WMmask = logical(WMmask.*brainmask); 
CSFmask = logical(CSFmask.*brainmask); 

for i=1:size(data,4)
    dummy=squeeze(data(:,:,:,i));  
    mean_cbf_gm(i)=nanmean(dummy(GMmask));    
    if isnan(mean_cbf_gm(i))
    error(['NaN value found in meanCBF volume : ' num2str(i)])
    elseif isinf(mean_cbf_gm(i))
    disp(['Inf value found in meanCBF volume : ' num2str(i)])
    disp(['Setting Inf values to zero for ' num2str(nnz(isinf(dummy))) ' voxels']);
    dummy(isinf(dummy))=0;    
    mean_cbf_gm(i)=nanmean(dummy(GMmask));    
    end
    data(:,:,:,i)=dummy;
end

mu_cbf=median(mean_cbf_gm);
std_cbf=1.4826*mad(mean_cbf_gm,1); %median absolute deviation

step1=abs(mean_cbf_gm - mu_cbf)<=std_cbf*2.5;
data_step1=data(:,:,:,step1);
disp(['Step1: Volume(s) removed (|meanCBF - mu| > 2.5*std): ' num2str(find(step1==0))]);
Iremoved_array=find(step1==0);
Nremoved_step1=sum(step1==0);
mean_cbf=nanmean(data_step1,4);

var_gm=nanvar(mean_cbf(GMmask));
N_gm=length(mean_cbf(GMmask))-1;%unbiased version for pooled variance

if nargin > 3
    var_csf=nanvar(mean_cbf(CSFmask));
    var_wm=nanvar(mean_cbf(WMmask));
    N_csf=length(mean_cbf(CSFmask))-1;
    N_wm=length(mean_cbf(WMmask))-1;
    V = (N_gm*var_gm + N_csf*var_csf + N_wm*var_wm)/(N_gm + N_csf + N_wm); %pooled variance
    disp(' Using Gray Matter, White Matter and CSF Spatial Pooled Variance')
else
    V = var_gm; % variance
    disp(' Using Gray Matter, Spatial Variance')
end

Vprev=V + 0.01*V;
data_step2=data_step1;

mean_cbf_prev_mask=mean_cbf(brainmask);
disp(['Spatial Pooled Variance, iter = 0 : ' num2str(V)]);
iter=0;
Nremoved_step2=0;
while V < Vprev && size(data_step2,4) > 1
    Vprev=V;
    cbfvols_inmask=[];    
    iter=iter+1;
    for i=1:size(data_step2,4)
        dummy=data_step2(:,:,:,i);
        cbfvols_inmask(:,i)=dummy(brainmask);
    end
        R=zeros(1,size(cbfvols_inmask,2));
        for i=1:size(cbfvols_inmask,2)
            Rarray=corrcoef(cbfvols_inmask(:,i),mean_cbf_prev_mask, 'rows','complete'); % works with NaN entries
            R(i)=Rarray(2);
        end        
        data_step3=data_step2;
        dummy2=data_step3(:,:,:,find(R==max(R)));
        meancbf_removed=nanmean(dummy2(GMmask));
        data_step3(:,:,:,find(R==max(R)))=[];% throw out volume with max corr, but only if spatial variance increases
        mean_cbf_prev=nanmean(data_step3,4);
        mean_cbf_prev_mask=mean_cbf_prev(brainmask);
        var_gm=nanvar(mean_cbf_prev(GMmask));
        N_gm=length(mean_cbf_prev(GMmask))-1;%unbiased version for pooled variance
        
        if nargin >3
            var_csf=nanvar(mean_cbf_prev(CSFmask));
            var_wm=nanvar(mean_cbf_prev(WMmask));
            N_csf=length(mean_cbf_prev(CSFmask))-1;
            N_wm=length(mean_cbf_prev(WMmask))-1;
            V = (N_gm*var_gm + N_csf*var_csf + N_wm*var_wm)/(N_gm + N_csf + N_wm); %pooled variance
        else
            V = var_gm; % variance
        end
        if V < Vprev
            dummy2=data_step2(:,:,:,find(R==max(R)));
            meancbf_removed=nanmean(dummy2(GMmask));
            Iremoved=find(meancbf_removed==mean_cbf_gm);
            data_step2=data_step3;
            Nremoved_step2=Nremoved_step2+1;                   
            disp(['Spatial Pooled Variance, iter = ' num2str(iter) ' : ' num2str(V)]); 
            disp(['Step2: Volume(i) removed = ' num2str(Iremoved)]);
            Iremoved_array=[Iremoved_array Iremoved];
        else
            disp(['Spatial Pooled Variance, iter = ' num2str(iter) ' : ' num2str(V)]); 
            disp(['Step2: Pooled Variance Increased, STOPPED ']); 
        end
end
disp(['Total number of removed volumes step1: ' num2str(Nremoved_step1)])
disp(['Total number of removed volumes step2: ' num2str(Nremoved_step2)])
disp(['Removed volumes all steps: ' num2str(sort(Iremoved_array))])

% jet_black(1,:)=[0 0 0];
% CBFlimmap=[0 65];% 
% figure, 
% subplot 121, montage(rot90(nanmean(data,4).*brainmask),[5,4]); caxis(CBFlimmap); colormap(jet_black);%
% subplot 122, montage(rot90(nanmean(data_step2,4).*brainmask),[5,4]); caxis(CBFlimmap); colormap(jet_black);%

output=data_step2*normfactor; % unnormalize to go back to original deltaM  values
end

