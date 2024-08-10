% function to fit monoexponential decay

function F = T1myfun(x,xdata);
% F = x(1)*(exp((-xdata)/x(2)));
% F = x(1)*(1 - exp(-(xdata/x(2))));
% F = x(1)*(1 - 2*exp(-xdata/x(2)));
% F = x(1)+x(3)*(1-exp(-xdata/x(2)));
%F = x(1)*(1-2*x(3)*exp(-xdata/x(2)));
 
 %Use the bruker fitting function
 F = x(1)+abs(x(3)*(1-2*exp(-xdata/x(2))));