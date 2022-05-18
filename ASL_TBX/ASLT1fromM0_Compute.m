function T1fromM0  = ASLT1fromM0_Compute(data,mask, pld_range)
% ASL Script, Siero 2019 - 01-03-2019
%compute T1w image from multi-delay PCASL (Look-Locker)
%data M0_combined_cphases
%apply T1 fit

dims=size(data);
data_2D=reshape(data, dims(1)*dims(2)*dims(3),dims(4));
%take log of data
data_2D=log(data_2D);
timearray=pld_range'; %s

const_array=ones(size(data_2D,2),1 );
Rfit=zeros(size(data_2D,1),2);
warning off
for i=1:size(data_2D,1)
A = [ const_array, data_2D(i,:)'];
Rfit(i,:)=A\timearray;
end
warning on

data_Rfit1=reshape(Rfit(:,1),dims(1),dims(2),dims(3));
data_Rfit2=reshape(Rfit(:,2),dims(1),dims(2),dims(3));
data_Rfit1_brain=data_Rfit1.*mask;
data_Rfit2_brain=-1/data_Rfit2.*mask*1e3;
data_Rfit2_brain(isnan(data_Rfit2_brain))=0;
data_Rfit2_brain_mask_high = data_Rfit2_brain<=300;
data_Rfit2_brain_mask_low = data_Rfit2_brain>0;
T1fromM0 = data_Rfit2_brain .*data_Rfit2_brain_mask_high.*data_Rfit2_brain_mask_low;
