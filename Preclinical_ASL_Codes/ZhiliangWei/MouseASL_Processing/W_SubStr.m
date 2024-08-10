function y=W_SubStr(strA,strB)
% Return 1 when one string is a component of the other
% By Zhiliang Wei, Mar 7, 2017
ScaleA=length(strA);
ScaleB=length(strB);
y=0;
% Switch to ensure strA is longer than strB
if ScaleA<ScaleB
    temp=strA;
    strA=strB;
    strB=temp;
    
    temp=[];
    temp=ScaleA;
    ScaleA=ScaleB;
    ScaleB=temp;
end
% Search strB in strA in a loop
for ni=1:ScaleA-ScaleB+1
    if strcmp(strA(ni:ni+ScaleB-1),strB)
        y=1;
        break;
    end
end
end

