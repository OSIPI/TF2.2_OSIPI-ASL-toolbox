function[T1,T1_TT]=T1fit(xdata,ydata)

%Calculate T1
% set X data (Echo Time)
% set Y data (Signal amplitude - noise)

% fit the data
rip = 0 ;
exitflag = 0;
A = max(ydata);
x0 = [0 1.7 A];
        
for rip =1:3
% fitting of the curve with 'myfun' that is,in this case, a monoexponential function
    %options=optimset('LargeScale','off','LevenbergMarquardt','on');
    %[x_bef,resnorm,residual,exitflag,output] = lsqcurvefit('T1myfun_TT', x0, xdata, ydata,[],[],options);
    [x_bef,resnorm,residual,exitflag,output] = lsqcurvefit('T1myfun', x0, xdata, ydata);
    b = x_bef; 
    x0 = b;    
end

y2 = T1myfun(x_bef,xdata);
T1 = b(2);
YYY = find(y2 == 0);
T1_TT = 1.443;
%Scatter plot of fitting and data-point
scatter(xdata,ydata);
 
hold on
plot(xdata,abs(y2),'b')
