close all
clear
clc

%% PAR File lines:
% 1-11 = Data Description
% 12-47 = General Information
% 48-52 = Pixel Values
% 53-97 = Image Information Definition
% 98-100 = Header von "Image Information"
% 101-end = real Image part


%% ASL File
%%%%%%%%%%%%%%%%%%%%%%% User Input %%%%%%%%%%%%%%%%%%%%%%%%%%%%%
filename   = 'ASL2_6_1';   % Name of file to be opened
%%%%%%%%%%%%%%%%%%%%%%% User Input %%%%%%%%%%%%%%%%%%%%%%%%%%%%%

% %%%%Read image parameter from PAR file%%%%
parrawdata = textscan(fopen([filename '.PAR']),'%s', 'delimiter', '\n');
pardata=parrawdata{1};

% %%%%Read relevant image acquisition parameters%%%%

for cntr=12:47 % reads number of slices
    temp = strread(pardata{cntr},'%s', 'delimiter', ':');
    temp2 = temp{1};
    if (temp2(1) == '#')
        continue % Ignore comments
    end
    if (strfind(temp2,'Max. number of slices/locations')>1)
        NSlices = str2double(temp{2}); 
     end
end

for cntr=12:47 % reads number of dynamics
    temp = strread(pardata{cntr},'%s', 'delimiter', ':');
    temp3 = temp{1};
    if (temp3(1) == '#')
        continue % Ignore comments
    end
    if (strfind(temp3,'Number of label types   <0=no ASL>')>1)
        NDynamics = str2double(temp{2}); 
     end
end

for cntr=12:47 % reads number of dynamics
    temp = strread(pardata{cntr},'%s', 'delimiter', ':');
    temp4 = temp{1};
    if (temp4(1) == '#')
        continue % Ignore comments
    end
    if (strfind(temp4,'Max. number of cardiac phases')>1)
        NPhases = str2double(temp{2}); 
     end
end

% %%%%choose line where the slice information starts%%%%

centr   = 101;
Lastline = size(pardata,1)-1;
%temp   = strread(pardata{cntr},'%s');


% %%%%read out the important values%%%%
% %%%%counting begins after the header (line 101)%%%%
for cntr=101:Lastline
    param = strread(pardata{centr},'%f');
    
    RI          = param(12);
    RS          = param(13);
    SS          = param(14);
    
    xRes        = param(10);
    yRes        = param(11);
    
end
Itype       = 4;
clear parrawdata;
clear pardata;

% %%%%Calculations as described in PAR file:%%%%

% DV = PV * RS + RI
% FP = DV / RS * SS

% %%%%ASLdata: read full data%%%%
recrawdata = fopen([filename '.REC'],'r');

% %%%%"Put" full dataset into an x-dimensional Array seperated by the Imagetypes:%%%%%
% %%%%0 = Magnitude, 1 = Real, 2 = Imaginary, 3 = Phase%%%%%

h = waitbar(0,'Separating Image Types');

for x = 0:Itype
    
   if x == 0
        ASLdatamag  = (reshape(fread(recrawdata,xRes*yRes*NDynamics*NSlices*NPhases,'int16'),xRes,yRes,2,NDynamics/2,NSlices,NPhases));
   end
    waitbar(x/Itype)
end
close(h)

clear recrawdata;
% %%%%The ASLdata is the image structure of the files. The resulting image looks like this: %%%%

% %%%%[Number of Rows, Number of Columns,2, Number of the "Dynamics" (Labeltypes), Slice Number, (Cardiac) Phase number]%%%%


% %%%%MAGNITUDE IMAGES%%%%


% %%%%separate even and odd numbered Labels (odd = tag, even = control)%%%%

even = ASLdatamag(:,:,2,:,:,:);

odd = ASLdatamag(:,:,1,:,:,:);

%recalculate the values as described in PAR file

clear ASLdatamag;

PV_odd = odd*RS+RI;
PV_even = even*RS+RI;
FP_odd = PV_odd/(RS*SS);
FP_even = PV_even/(RS*SS);

clear even;
clear odd;
clear PV_odd;
clear PV_even;
% %%%%preallocating for speed%%%%

even_acc=zeros(xRes,yRes,NSlices,NPhases);
odd_acc=zeros(xRes,yRes,NSlices,NPhases);

% %%%%add up all even and odd images%%%%

for x=1:xRes
    for y=1:yRes
        for z=1:NSlices
            for t=1:NDynamics/2
                for u = 1:NPhases
                even_acc(x,y,z,u)=even_acc(x,y,z,u)+FP_even(x,y,t,1,z,u);
                end
            end
        end
    end
end

for x=1:xRes
    for y=1:yRes
        for z=1:NSlices
            for t=1:NDynamics/2
                for u = 1:NPhases
                odd_acc(x,y,z,u)=odd_acc(x,y,z,u)+FP_odd(x,y,t,1,z,u);
                end
            end
        end
    end
end

% %%%%perform the subtraction%%%%
sub=odd_acc - even_acc;

clear even_acc;
clear odd_acc;
% %%%%Save images in Nifti Format%%%%

h = waitbar(0,'Magnitude');

for x = 1:NPhases
    
    waitbar(x/NPhases)
    
    if x == 1
        sub1 = sub(:,:,:,1);
        
        origin = [1 1 1]; datatype = 64;
        nii = make_nii(sub1, [], origin, datatype);
        save_nii(nii,'Angiomag1.nii');
    end
    
    if x == 2
        sub2 = sub(:,:,:,2);
        
        origin = [1 1 1]; datatype = 64;
        nii = make_nii(sub2, [], origin, datatype);
        save_nii(nii,'Angiomag2.nii');
    end
    
    if x == 3
        sub3 = sub(:,:,:,3);
        
        origin = [1 1 1]; datatype = 64;
        nii = make_nii(sub3, [], origin, datatype);
        save_nii(nii,'Angiomag3.nii');
    end
    
    if x == 4
        sub4 = sub(:,:,:,4);
        
        origin = [1 1 1]; datatype = 64;
        nii = make_nii(sub4, [], origin, datatype);
        save_nii(nii,'Angiomag4.nii');
    end
    
    if x == 5
        sub5 = sub(:,:,:,5);
        
        origin = [1 1 1]; datatype = 64;
        nii = make_nii(sub5, [], origin, datatype);
        save_nii(nii,'Angiomag5.nii');
        
    end
    
    if x == 6
        sub6 = sub(:,:,:,6);
        
        origin = [1 1 1]; datatype = 64;
        nii = make_nii(sub6, [], origin, datatype);
        save_nii(nii,'Angiomag6.nii');
        
    end
    
    if x == 7
        sub7 = sub(:,:,:,7);
        
        origin = [1 1 1]; datatype = 64;
        nii = make_nii(sub7, [], origin, datatype);
        save_nii(nii,'Angiomag7.nii');
        
    end
    
    if x == 8
        sub8 = sub(:,:,:,8);
        
        origin = [1 1 1]; datatype = 64;
        nii = make_nii(sub8, [], origin, datatype);
        save_nii(nii,'Angiomag8.nii');
        
    end
end

close(h)

