function [PDimg, CBFimg] = ASL_CBF(path, maskStatus, indexRange)

% maskStatus:
% 0: No mask/ROI file exists
% 1: Mask/ROI file exists and will display the ROI
% indexRange: range of slices to be displayed
    
    
        % Paths  
         outpath = [path '/' 'ASL.mat'];
         maskpath = [path '/' 'MASK.mat'];
    
         if maskStatus == 0
            load(outpath)
         elseif maskStatus == 1
            load(outpath)
            load(maskpath, 'ROI')
         end
       

    NX = size(diffmap,1);
    NY = size(diffmap,2);
    Nslice = size(diffmap,3);
         
    % Calculate the CBF values
    lamda=0.9;
    AILLI=0.5; 
    
    %this labeling efficency need to be calabrate using global  CBF. it depends
    %on the puslse train and hardware. usually it is 0.5
    %Age-Related Alterations in Brain Perfusion, Venous Oxygenation, and Oxygen Metabolic Rate of Mice: A 17-Month Longitudinal MRI Study
    %Zhiliang Wei,Lin Chen, Xirui Hou, Peter C. M. van Zijl,Jiadi Xu, and Hanzhang Lu
    %Front Neurol. 2020; 11: 559.
    %doi: 10.3389/fneur.2020.00559
    
     % Calculate CBF values
      for i=1:Nslice
         CBF(:,:,i)=6000*lamda*diffmap(:,:,i)./(100*AILLI);
         CBF(:,:,i) = rot90(CBF(:,:,i),2);
         M0img(:,:,i)=rot90(M0img(:,:,i),2); 
    
      end
    
      M0img = M0img(:,:,indexRange);
      PDimg = reshape(M0img,NX,NY*[]);
      CBF = CBF(:,:, indexRange); 
      CBFimg=reshape(CBF,NX,NY*[]);
    
      if maskStatus == 0
        return
    
      elseif maskStatus == 1
        ROI = ROI(:, :, indexRange);
        MaskAll = reshape(ROI,NX,NY*[]);
        masktmp = MaskAll;
        masktmp2 = ~masktmp;
        CBFimg( masktmp2 ) = 0; 
    
      end
   