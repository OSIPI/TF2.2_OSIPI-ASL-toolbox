%% Function description LZ 2021-04-16
% INPUT: CTRL and TAG are matrix values from the control and label images of
% ASL images, method can be any value as shown in the code
% OUTPUT: output will be a matrix for difference images

% Example: output=ASLDeltaM(CTRL,TAG,'PairWise');
%%
function output=ASLDeltaM(CTRL,TAG,method)
% ASL Script, Siero 2019 - 01-03-2019
dm=[];
temp=[];
dims=size(CTRL);
nvols=size(CTRL,4);

if isempty(TAG)
% Splitting interleaved CTRLTAG data in separate CTRL and TAG arrays..
    nvols =nvols/2;
    data = CTRL;
    CTRL = data(:,:,:,2*(1:nvols) - 1);
    TAG = data(:,:,:,2*(1:nvols));
end

if strcmp(method,'SurroundSubtract')
    % treat first and last volume separately
    dm(:,:,:,1)=CTRL(:,:,:,1) - TAG(:,:,:,1);
    dm(:,:,:,2*nvols)=CTRL(:,:,:,end) - TAG(:,:,:,end);
    for j = 1:nvols-1
        temp = (CTRL(:,:,:,j) + CTRL(:,:,:,j+1))/2;
        dm(:,:,:,2*j) = temp - TAG(:,:,:,j+1);
        temp = (TAG(:,:,:,j) + TAG(:,:,:,j+1))/2;
        dm(:,:,:,2*j+1) = CTRL(:,:,:,j) - temp;
    end
elseif strcmp(method,'ObtainBOLD')
  % sliding window average (2 volumes) 
  % treat first and last volume separately
    dm(:,:,:,1)=CTRL(:,:,:,1) + TAG(:,:,:,1);
    dm(:,:,:,2*nvols)=CTRL(:,:,:,end) + TAG(:,:,:,end);
    for j = 1:nvols-1
        temp = (CTRL(:,:,:,j) + CTRL(:,:,:,j+1))/2;
        dm(:,:,:,2*j) = temp + TAG(:,:,:,j+1);
        temp = (TAG(:,:,:,j) + TAG(:,:,:,j+1))/2;
        dm(:,:,:,2*j+1) = CTRL(:,:,:,j) + temp;
    end
    dm=dm/2; %for taking the average
end

if strcmp(method,'PairWise')
    dm = CTRL - TAG;
elseif strcmp(method,'BOLDPairWise')
    dm = (CTRL + TAG)/2;
end
output=dm;