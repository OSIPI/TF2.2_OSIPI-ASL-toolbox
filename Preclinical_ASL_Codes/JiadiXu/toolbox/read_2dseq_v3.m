
function [img Ncolumns  Nrows  NI NR RecoNumInputChan]= read_2dseq_v3(fname, expno, procno)

% 
%% Authors:Jiadi Xu, Xu Li (xuli@mri.jhu.edu),Song XiaoLei
% Affiliation: Radiology @ JHU; Kennedy Krieger Institute
% 
% read image data in file "2dseq" reconstructed from Bruker ParaVision 5
% the file is in the directory <fname>/<expno>/pdata/<procno>/2dseq
% 
% certain acquision and reconstruction parameters are stored in the
% following files: 
%  <fname>/<expno>/acqp:    acquisition parameter
%  <fname>/<expno>/fid:     raw data
%  <fname>/<expno>/method:  PVM method paramter
%  <fname>/<expno>/pdata/<procno>/reco:  reconstruction parameter
% 
%   Image Size = sizeof(word)*NR*NI*RECO_size
%       where
%   NR: repetition time (dynamics)
%   NI: slice number X echo number
%   RECO_size: Nx*Ny*Nz
%
%   parameters extracted from 'method': READDIRECTION
%   parameters extracted from 'acqp':   NI, NR, NSLICES, NECHOES
%   parameters extracted from 'reco':   RECOSIZE, WordType, ByteOrder, 
%                                       MapMode, MapOffset, MapSlope
%   img array:  [Nrow, Ncolum, NI NR, RecoNumInputChan]

method_file = [ fname filesep num2str(expno) filesep 'method'];
acqp_file = [ fname filesep num2str(expno) filesep 'acqp'];
reco_file = [ fname filesep num2str(expno) filesep 'pdata' filesep, num2str(1), filesep 'reco'];
img_name = [ fname filesep num2str(expno) filesep 'pdata' filesep, num2str(procno), filesep '2dseq'];

method_par=readnmrpar(method_file);
acqp_par=readnmrpar(acqp_file);
reco_par=readnmrpar(reco_file);

%% read paramters from method file

para_list = fopen(method_file);
if para_list == -1;
    error('Could not open method file');
end

READDIRECTION=method_par.PVM_SPackArrReadOrient;


%% read paramters from acqp file

para_list = fopen(acqp_file);
if para_list == -1;
    error('Could not open acqp file');
end
NI=acqp_par.NI;
NR=acqp_par.NR;
NSLICES=acqp_par.NSLICES;
NECHOES=acqp_par.NECHOES;


%% read paramters from reco file

para_list = fopen(reco_file);
if para_list == -1;
   error('Could not open reco file');
end
RECOSIZE=reco_par.RECO_size;
Nrows=RECOSIZE(1);
Ncolumns = RECOSIZE(2);
      if length(RECOSIZE) > 2       
            NSLICES = RECOSIZE(3);                      % for 3D sequence
      end
      
WORDTYPE=reco_par.RECO_wordtype;
BIT = ['int', WORDTYPE(2:3)]; 
BYTEORDER =reco_par.RECO_byte_order;
RECOMAPMODE=reco_par.RECO_map_mode;
    
RECOMAPOFFSET=reco_par.RECO_map_offset;
RECOMAPOFFSET = RECOMAPOFFSET(1);   
RECOMAPSLOPE=reco_par.RECO_map_slope;
RECOMAPSLOPE = RECOMAPSLOPE(1);
%RecoNumInputChan=reco_par.RecoNumInputChan;  
RecoNumInputChan=1;
%RecoCombineMode=reco_par.RecoCombineMode;   
RecoCombineMode='Sum';
    



%% read image data

Bruker_recon = fopen(img_name,'r', BYTEORDER(1));
if Bruker_recon==-1;
    error('Could not open 2dseq file');
end
        sizeD3 = NSLICES;
        sizeD4 = NR;
        sizeD5 = 1;

if strcmpi(RecoCombineMode, 'ShuffleImages')
         sizeD5 = RecoNumInputChan;
end
sizeRecAll=  [Nrows, Ncolumns,sizeD3, sizeD4,sizeD5];
img = zeros(sizeRecAll);


for ii = 1:sizeD5
    for jj = 1:sizeD4
        for kk = 1:sizeD3
           
                img(:,:,kk,jj,ii) = fread(Bruker_recon, [Nrows, Ncolumns], BIT);    % read in slice by slice

        end        
    end
end



fclose(Bruker_recon);


%% Scaling and permutation

        img = img./RECOMAPSLOPE + RECOMAPOFFSET;          % absolute mapping scaling             
       img = permute(img, [2, 1, 3:length(size(img))]);        % permute

img=img*100.0/acqp_par.RG;

end

function P = readnmrpar(FileName)
% RBNMRPAR      Reads BRUKER parameter files to a struct
%
% SYNTAX        P = readnmrpar(FileName);
%
% IN            FileName:	Name of parameterfile, e.g., acqus
%
% OUT           Structure array with parameter/value-pairs
%

% Read file
A = textread(FileName,'%s','whitespace','\n','bufsize', 4096*4);

% Det. the kind of entry
TypeOfRow = cell(length(A),2);
    
R = {   ...
    '^##\$*(.+)=\ ?\([\ \d\.]+\)(.+)', 'ParVecVal' ; ...
    '^##\$*(.+)=\ ?\([\ \d\.]+\)$'   , 'ParVec'    ; ...
    '^##\$*(.+)=\ ?(.+)'             , 'ParVal'    ; ...
    '^([^\$#].*)'                   , 'Val'       ; ...
    '^\$\$(.*)'                     , 'Stamp'     ; ...
    '^##\$*(.+)='                   , 'EmptyPar'  ; ...
	'^(.+)'							, 'Anything'	...
    };

for i = 1:length(A)
    for j=1:size(R,1)
        [s,t]=regexp(A{i},R{j,1},'start','tokens');
        if (~isempty(s))
            TypeOfRow{i,1}=R{j,2};
            TypeOfRow{i,2}=t{1};
        break;
        end
    end
end

% Set up the struct
i=0;
while i < length(TypeOfRow)
    i=i+1;
    switch TypeOfRow{i,1}
        case 'ParVal'
            LastParameterName = TypeOfRow{i,2}{1};
            P.(LastParameterName)=TypeOfRow{i,2}{2};
        case {'ParVec','EmptyPar'}
            LastParameterName = TypeOfRow{i,2}{1};
            P.(LastParameterName)=[];
        case 'ParVecVal'
            LastParameterName = TypeOfRow{i,2}{1};
            P.(LastParameterName)=TypeOfRow{i,2}{2};
        case 'Stamp'
            if ~isfield(P,'Stamp') 
                P.Stamp=TypeOfRow{i,2}{1};
            else
                P.Stamp=[P.Stamp ' ## ' TypeOfRow{i,2}{1}];
            end
        case 'Val'
			if isempty(P.(LastParameterName))
				P.(LastParameterName) = TypeOfRow{i,2}{1};
			else
				P.(LastParameterName) = [P.(LastParameterName),' ',TypeOfRow{i,2}{1}];
			end
        case {'Empty','Anything'}
            % Do nothing
    end
end
    

% Convert strings to values
Fields = fieldnames(P);

for i=1:length(Fields);
    trystring = sprintf('P.%s = [%s];',Fields{i},P.(Fields{i}));
    try
        eval(trystring);
	catch %#ok<CTCH>
        % Let the string P.(Fields{i}) be unaltered
    end
end
end