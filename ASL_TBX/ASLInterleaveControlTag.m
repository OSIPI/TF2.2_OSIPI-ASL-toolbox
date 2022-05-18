function output=ASLInterleaveControlTag(CTRL,TAG)
% ASL Script, Siero 2019 - 01-03-2019
% The purpose is to interleave the individual CTRL and TAG data into order like this: CTRL1..TAG1..CTRL2..TAG2..
% Input: the .mat data of control and label
% Output: the .mat data containing control and label with order like this: CTRL1..TAG1..CTRL2..TAG2..
% 

CTRLTAG=[];
dims = size(CTRL);% xdim y xim zdim tdim asl_label

odd_index=2*(1:dims(4)) - 1;
even_index=2*(1:dims(4));

if(nargin ==1)
    data=CTRL;
    if length(size(data))<5
        disp('WARNING probably single slice data!')
    end
    CTRLTAG(:,:,:,odd_index)=data(:,:,:,:,1);
    CTRLTAG(:,:,:,even_index)=data(:,:,:,:,2);
elseif(nargin ==2)
    CTRLTAG(:,:,:,odd_index)=CTRL;
    CTRLTAG(:,:,:,even_index)=TAG;
end

output=CTRLTAG;