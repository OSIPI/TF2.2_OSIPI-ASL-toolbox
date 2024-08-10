function [diffmap, dyncheck, dyncheck2] = ASL_Preparation(selected_path)

try 
    % Inputted path
    path2 = selected_path;
    
    % Deleting the expno from the path
    parentPath = fileparts(path2);
    
    % Deleting the folder that contained expno from the path
    parentPath2 = fileparts(parentPath);
   
    % Replacing with spm8 library
    newPath = strcat(parentPath2, '/spm8');
    
    % Adding spm8 to path
    addpath(newPath);
    
    pathString = selected_path;
    [path, expno] = fileparts(pathString);      
    [imgs] = read_2dseq_v3(path,expno,1);

    methodfile = [selected_path '/method'];
    Pars = readnmrpar(methodfile);

    outpath= selected_path;


    mkdir(outpath);
    NX=size(imgs,1);
    NY=size(imgs,2);
    NI=size(imgs,3);
    NR=size(imgs,4);
  
    %covariance correction

    iref=1;
    for j=1:Pars.NRep
        %remove first points of control and label
        REFFUN(iref)=0;
        iref=iref+1;
        for i=2:Pars.NControl
            REFFUN(iref)=1;
            iref=iref+1;
        end
        REFFUN(iref)=0;
        iref=iref+1;
        for i=2: Pars.NLabel
            REFFUN(iref)=-1;
            iref=iref+1;
        end
    end

% get M0
M0img=zeros(NX,NY,NI);
    
for i=2:NR
     M0img=M0img+imgs(:,:,:,i);  
end

M0img=M0img./(NR-1);


for ix=1:NX
   for iy=1:NX
    for ini=1:NI
    didx=1;
    for i=1:NR
        dyn(didx,1)=100*imgs(ix,iy,ini,i)/M0img(ix,iy,ini);
        didx=didx+1;
    end
  
    % high pass filter to remove drift
    K.RT = Pars.PVM_RepetitionTime/1000.0;
    K.row = 1:NR-1; % 130 corresponds to the length of convreg
    K.HParam = (Pars.NControl+Pars.NLabel)*K.RT*3; % cut-off period in minutes
    nK = spm_filter(K);
    dyn = spm_filter(nK, dyn);
    
    didx=1;
    for i=1:NR
        dyn(didx,1)=REFFUN(didx)*dyn(didx,1);
        didx=didx+1;
        
    end
    diffmap(ix,iy,ini)=sum(dyn)/(didx-1-Pars.NRep*2);

end
end
end


% dynamic check if any drift
Nslice=2;
for i=2:NR
dyncheck(i-1,1)=sum(sum(imgs(:,:,Nslice,i),'omitnan'))/sum(sum(M0img(:,:,Nslice),'omitnan'));
end
    K.RT = Pars.PVM_RepetitionTime/1000.0;
    K.row = 1:NR-1; % 130 corresponds to the length of convreg
    K.HParam = (Pars.NControl+Pars.NLabel)*K.RT*3; % cut-off period in minutes
    nK = spm_filter(K);
    dyncheck2 = spm_filter(nK, dyncheck);

    outfile=[outpath '/ASL' ];

    save(outfile,'diffmap','M0img','dyncheck2','dyncheck');

catch
    msgbox("Error: The selected file cannot be prepared");
   
end
end

