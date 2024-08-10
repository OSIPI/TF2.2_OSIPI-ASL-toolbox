function y=W_MSplot(data,winf,choice,range)
% showing the multi-slice data into a single window
% data should be a 3D matrix with 3rd dimension denoting the slices
% winf represents the numbers of subplots in a row and a column
if nargin==2
    choice=0;
end
scale=size(data);
target=zeros(winf(1)*scale(1),winf(2)*scale(2));
for ni=1:scale(3)
    pi=floor((ni-1)/winf(2));
    qi=ni-pi*winf(2);
    target(pi*scale(1)+1:(pi+1)*scale(1),(qi-1)*scale(2)+1:qi*scale(2))=data(:,:,ni);
end
if choice==1
    figure;imshow(target,range,'initialmag','fit');
end
y=target;
end