function y=W_Expno(path)
% Automatic extracting the expno from a directory
Temp=dir(path);
Scale=size(Temp,1);
Expno=[];
for ni=1:Scale
    Expno=[Expno str2num(Temp(ni).name)];
end
y=sort(Expno,'descend');
end
