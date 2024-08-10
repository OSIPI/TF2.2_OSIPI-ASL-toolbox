function y=W_ImgParaAbs(path)
% Abstracting imaging slice information from the BRUKER data
% Programmed by Zhiliang Wei on July 3rd, 2016 at Park Building 
% The Johns Hopkins University
TIME=cputime;
Slice.path=path(1:end);
% Initial the parameters
Slice.slicenum=0;
Slice.size=[];
Slice.thickness=0;
Slice.tr=0;
Slice.te=0;
Slice.ROI=[];
Slice.Unit=[];
Slice.Protocol=[];
Slice.eTE=[];
Slice.EchoNum=[];
Slice.SlabMargin=[];
Slice.PostLabelTime=[];
Slice.Segment=[];
Slice.Scan=[];
Slice.AcqSize=[];
Slice.NR=[];
Slice.VENC=[];
Slice.rep=[];
Slice.asllabel=[];
Slice.aslPLD=[];
Slice.aslLD=[];
% <----------------------- ACQP --------------------->
path1=[path filesep 'acqp'];
if exist(path1)
filepath=fopen(path1);
while ~feof(filepath)
    temp=fscanf(filepath,'%s',1);
    % 1 for scan name
    if strcmp('##$ACQ_scan_name=(',temp)==1
        for ContCount=1:3
            temp=fscanf(filepath,'%s',1);
        end
        Slice.Scan=temp(2:end);
    % 2 for protocol
    elseif strcmp('##$ACQ_protocol_name=(',temp)==1
        for ContCount=1:3
            temp=fscanf(filepath,'%s',1);
        end 
        Slice.Protocol=temp;
    % 3 ROI size
    elseif strcmp('##$ACQ_fov=(',temp)==1
        temp=fscanf(filepath,'%s',1);
        Cont=str2num(temp);
        temp=fscanf(filepath,'%s',1);
        for ContCount=1:Cont
            temp=fscanf(filepath,'%s',1);
            Slice.ROI(ContCount)=str2num(temp);
        end 
    elseif strcmp('##$ACQ_slice_offset=(',temp)==1
        temp=fscanf(filepath,'%s',1);
        Slice.slicenum=str2num(temp);
    % 4 Slice thickness
    elseif W_strcmp('##$ACQ_slice_thick=',temp)==1
         Slice.thickness=str2num(temp(20:end));
    % 5 Repetition time
    elseif strcmp('##$ACQ_repetition_time=(',temp)==1
         temp=fscanf(filepath,'%s',1);
         temp=fscanf(filepath,'%s',1);
         temp=fscanf(filepath,'%s',1);
         Slice.tr=str2num(temp); 
         Slice.tr=W_DigitS(Slice.tr,2);
         Slice.tr=str2num(temp);
    % 5 Echo time
    elseif strcmp('##$ACQ_echo_time=(',temp)==1
         temp=fscanf(filepath,'%s',1);
         temp=fscanf(filepath,'%s',1);
         temp=fscanf(filepath,'%s',1);
         Slice.te=str2num(temp); 
         Slice.te=W_DigitS(Slice.te,2);
         Slice.te=str2num(Slice.te);
    % 6 Matrix size
    elseif strcmp('##$ACQ_size=(',temp)==1
        temp=fscanf(filepath,'%s',1);
        Cont=str2num(temp);
        temp=fscanf(filepath,'%s',1);
        for ContCount=1:Cont
            temp=fscanf(filepath,'%s',1);
            Slice.AcqSize(ContCount)=str2num(temp);
        end
    % 7 Number of repetitions
    elseif W_strcmp('##$NR=',temp)==1
         Slice.NR=str2num(temp(7:end));
    end
end
fclose(filepath);
else
    disp([path1 ' not found']);
end

%<------------------------ Method -------------------->
path1=[path filesep 'method'];
if exist(path1)
filepath=fopen(path1);
while ~feof(filepath)
    temp=fscanf(filepath,'%s',1);
    % 1 Effective echo time
    if strcmp('##$TotalEchoTime=(',temp)==1
        temp=fscanf(filepath,'%s',1);
        Cont=str2num(temp);
        temp=fscanf(filepath,'%s',1);
        for ContCount=1:Cont
            temp=fscanf(filepath,'%s',1);
            Slice.eTE(ContCount)=str2num(temp);
        end
    % 2 Number of echo
    elseif strcmp('##$NEcho=(',temp)==1
        temp=fscanf(filepath,'%s',1);
        Cont=str2num(temp);
        temp=fscanf(filepath,'%s',1);
        for ContCount=1:Cont
            temp=fscanf(filepath,'%s',1);
            Slice.EchoNum(ContCount)=str2num(temp);
        end
    % 3 Experimental duration
    elseif strcmp('##$PVM_ScanTimeStr=(',temp)==1
        temp=fscanf(filepath,'%s',1);
        temp=fscanf(filepath,'%s',1);
        temp=fscanf(filepath,'%s',1);
        Slice.ScanTime=temp(2:end-1); 
    % 4 Post labeling time
    elseif W_strcmp('##$PostLabelTime=',temp)==1
        Slice.PostLabelTime=str2num(temp(18:end));    
    % 5 Slab margin
    elseif W_strcmp('##$Slab_Margin=',temp)==1
        Slice.SlabMargin=str2num(temp(16:end));
    % 6 Segments
    elseif W_strcmp('##$NSegments',temp)==1
        Slice.Segment=str2num(temp(14:end));
    % 7 VENC
    elseif W_strcmp('##$FlowRange=',temp)==1
        Slice.VENC=str2num(temp(14:end));
    % 8 Number of repetition
    elseif W_strcmp('##$PVM_NRepetitions=',temp)==1
        Slice.rep=str2num(temp(21:end));
    % 9 Labeling duration
    elseif W_strcmp('##$PCASL_LabelTime=',temp)==1
        Slice.asllabel=str2num(temp(20:end));
    % 10 ASL PLD: Barbier's protocol
    elseif W_strcmp('##$PCASL_PostLabelTime=',temp)==1
        Slice.aslPLD=str2num(temp(24:end));
    % 11 ASL PLD: Wei's protocol
    elseif W_strcmp('##$PCASL_PLD=',temp)==1
        Slice.aslPLD=str2num(temp(14:end));
    % 12 ASL labeling duration: Wei's protocol
    elseif W_strcmp('##$PCASL_Dur=',temp)==1
        Slice.aslLD=str2num(temp(14:end));
    end

end
fclose(filepath);
else
    disp([path1 'not found']);
end

%<---------------------- Visu ---------------------->
path1=[path filesep 'visu_pars'];
if exist(path1)
filepath=fopen(path1);
while ~feof(filepath)
    temp=fscanf(filepath,'%s',1);
    % 1 Slice number
    if strcmp('##$VisuCoreSize=(',temp)==1
        temp=fscanf(filepath,'%s',1);
        Cont=str2num(temp);
        temp=fscanf(filepath,'%s',1);
        for ContCount=1:Cont
            temp=fscanf(filepath,'%s',1);
            Slice.size(ContCount)=str2num(temp);
        end
    % 7 for unit
    elseif strcmp('##$VisuCoreUnits=(',temp)==1
        Cont=str2num(fscanf(filepath,'%s',1));
        temp=fscanf(filepath,'%s',1);
        temp=fscanf(filepath,'%s',1);      
        for ContCount=1:Cont
            Slice.Unit{ContCount}=fscanf(filepath,'%s',1); 
        end
    end 
end
fclose(filepath);
else
    disp([path1 'not found']);
end

disp(['Time costing for parameter abstracting: ' num2str((cputime-TIME)) ' s...']);
y=Slice;
end

function y=W_strcmp(strA,strB)
% By Zhiliang Wei 08-19-2016, Johns Hopkins University
% strA can differ in size from strB, return 1 when strA or strB is
% consistent with a fraction of the other
scale=min([prod(size(strA)) prod(size(strB))]);
if scale==0
    y=0;
else
    if sum(abs(strA(1:scale)-strB(1:scale)))==0
        y=1;
    else
        y=0;
    end
end
end

    

