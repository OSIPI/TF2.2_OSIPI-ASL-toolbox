function ASL_calculateCBFmap(path_temp,asl_paras)
% This function obtains CBF value in the unit of ml/100g/min
% Peiying Liu, Oct 7, 2015; yli20151201

disp(['ASLMRICloud: (' asl_paras.SINGLPROC.name_asl ') Calculate CBF maps...']);

name_asl    = asl_paras.SINGLPROC.name_asl;

scan_mode   = asl_paras.BASICPARA.scan_mode;   
labl_schm   = asl_paras.BASICPARA.labl_schm;
casl_dur    = asl_paras.BASICPARA.casl_dur;
casl_pld    = asl_paras.BASICPARA.casl_pld; 
pasl_ti1    = asl_paras.BASICPARA.pasl_ti1;  
pasl_ti     = asl_paras.BASICPARA.pasl_ti; 
slic_dur    = asl_paras.BASICPARA.slic_dur;  

t1blood     = asl_paras.CBFQUANTI.t1_blood;
part_coef   = asl_paras.CBFQUANTI.part_coef;
labl_eff    = asl_paras.CBFQUANTI.labl_eff;
flag_bgs    = asl_paras.BGSUPPRES.flag_bgs;
bgsu_eff    = asl_paras.BGSUPPRES.bgsu_eff;
bgsu_num    = asl_paras.BGSUPPRES.bgsu_num;

applyBrnMsk = asl_paras.OTHERPARA.applyBrnMsk;

% load diff/m0map/brnmsk_dspl/brnmsk_clcu
fn_diff        = spm_select('FPList',path_temp,['^r',name_asl,'_diff.img$']);
fn_m0map       = spm_select('FPList',path_temp,['^r.*\_m0map.img$']);
fn_brnmsk_dspl = spm_select('FPList',path_temp,['^r.*\_brnmsk_dspl.img$']);
fn_brnmsk_clcu = spm_select('FPList',path_temp,['^r.*\_brnmsk_clcu.img$']);
diff        = spm_read_vols(spm_vol(fn_diff));        diff(isnan(diff))                = 0;
m0map       = spm_read_vols(spm_vol(fn_m0map));       m0map(isnan(m0map))              = 0;
brnmsk_dspl = spm_read_vols(spm_vol(fn_brnmsk_dspl)); brnmsk_dspl(isnan(brnmsk_dspl))  = 0;
brnmsk_clcu = spm_read_vols(spm_vol(fn_brnmsk_clcu)); brnmsk_clcu(isnan(brnmsk_clcu))  = 0;
brnmsk_dspl = logical(brnmsk_dspl);
brnmsk_clcu = logical(brnmsk_clcu);

% calculate absolute CBF without M0/mask/constant
% ref: ASL white paper
tmpcbf     = zeros(size(diff));
nslice     = size(tmpcbf,3);

switch labl_schm
    case 'pCASL'
        for kk = 1:nslice
            spld = casl_pld + slic_dur*(kk-1)*strcmp(scan_mode,'2D'); % correct delay for each slice
            tmpcbf(:,:,kk) = diff(:,:,kk)*exp(spld/t1blood)/(1-exp(-casl_dur/t1blood))/t1blood;
        end
    case 'PASL'
        for kk = 1:nslice
            sti = pasl_ti + slic_dur*(kk-1)*strcmp(scan_mode,'2D');
            tmpcbf(:,:,kk) = diff(:,:,kk)*exp(sti/t1blood)/pasl_ti1;
        end
    case 'VSASL' % Not deployed yet
        for kk = 1:nslice
            spld = casl_pld + slic_dur*(kk-1)*strcmp(scan_mode,'2D'); 
            tmpcbf(:,:,kk) = diff(:,:,kk)*2*exp(spld/t1blood)/spld; % Bipolar gradient is necessary??
        end
end

% normalize with M0/brain mask/other constant
m0map(abs(m0map)<1e-6) = mean(m0map(brnmsk_clcu)); % if border is missing due to motion and coreg

m0vol   = double(m0map);    
brvol   = double(brnmsk_dspl)*(applyBrnMsk==1) + ones(size(brnmsk_dspl))*(applyBrnMsk==0);

alpha    = (bgsu_eff^bgsu_num*flag_bgs + 1*~flag_bgs) * labl_eff;
cbf      = tmpcbf ./ m0vol .* brvol * part_coef/2/alpha*60*100*1000;

% threshold CBF image to remove the dark/bright spots
cbf_thr          = cbf;
cbf_thr(cbf<0)   = 0;
cbf_thr(cbf>200) = 200;
cbf_glo          = mean(cbf_thr(brnmsk_clcu));
rcbf_thr         = cbf_thr / cbf_glo;

% write absolute/relative CBF maps to temp path
ovol1       = spm_vol(fn_diff);
ovol2       = ovol1;
ovol1.fname = strcat(path_temp,filesep,'r',name_asl,'_aCBF_native.img');
ovol2.fname = strcat(path_temp,filesep,'r',name_asl,'_rCBF_native.img');
spm_write_vol(ovol1,  cbf_thr);
spm_write_vol(ovol2, rcbf_thr);

