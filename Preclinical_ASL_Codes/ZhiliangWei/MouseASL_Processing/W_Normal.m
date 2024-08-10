function y=W_Normal(xaxis,val)
% Fitting with the normal distribution function 
% y=coef(1)*exp(-(x-coef(2)).^2/2)
% Return the fitted parameters
fun = @ (beta,x)(beta(1)*exp(-0.5*(x-beta(2)).^2));
beta = nlinfit(xaxis,val,fun,[200 3]);
y.beta=beta;
y.val=beta(1)*exp(-0.5*(xaxis-beta(2)).^2);
end
